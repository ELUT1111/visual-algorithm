"""Aho-Corasick automaton for multi-pattern string matching."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class AhoCorasickAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="aho_corasick",
            category="tree",
            description="Build a trie with failure links and scan text for multiple patterns in one pass",
            emoji="AC",
            parameters=[
                {"name": "patterns", "type": "str", "required": True, "description": "Comma-separated patterns"},
                {"name": "text", "type": "str", "required": True, "description": "Text to search"},
            ],
            time_complexity="O(total pattern length + text length + matches)",
            space_complexity="O(total pattern length * alphabet)",
            layout="hierarchical",
            builds_structure=True,
            use_cases=[
                "Multi-pattern string matching",
                "Intrusion detection signature scans",
                "Antivirus pattern matching",
                "Dictionary keyword search",
                "DNA sequence matching",
            ],
            pseudocode=(
                "build trie from patterns\n"
                "root children fail to root\n"
                "BFS over trie nodes:\n"
                "    follow failure links until a transition exists\n"
                "    set child.fail and merge fail output\n"
                "scan text:\n"
                "    follow transitions or failure links\n"
                "    report every pattern in current output list"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        raw_patterns = str(params.get("patterns", "") or "")
        text = str(params.get("text", "") or "").strip().lower()
        patterns = [pattern.strip().lower() for pattern in raw_patterns.split(",") if pattern.strip()]
        if not patterns:
            return

        nodes: dict[str, dict] = {}
        counter = 0

        def make_node(char: str, parent: str | None = None, edge_char: str = "") -> str:
            nonlocal counter
            counter += 1
            node_id = f"ac{counter}"
            nodes[node_id] = {
                "id": node_id,
                "char": char,
                "children": {},
                "fail": None,
                "output": [],
                "direct_output": [],
                "parent": parent,
                "edge_char": edge_char,
            }
            return node_id

        root_id = make_node("*")
        nodes[root_id]["fail"] = root_id
        matches: list[dict] = []
        scan_trace: list[dict] = []
        failure_trace: list[dict] = []

        def automaton_state(extra: dict | None = None) -> dict:
            node_rows = {
                node_id: {
                    "char": node["char"],
                    "children": dict(sorted(node["children"].items())),
                    "fail": node["fail"],
                    "output": list(node["output"]),
                    "direct_output": list(node["direct_output"]),
                    "parent": node["parent"],
                    "edge_char": node["edge_char"],
                }
                for node_id, node in nodes.items()
            }
            payload = {
                "patterns": list(patterns),
                "text": text,
                "root": root_id,
                "node_count": len(nodes),
                "failure_links": {node_id: node["fail"] for node_id, node in nodes.items() if node["fail"] is not None},
                "output_table": {node_id: list(node["output"]) for node_id, node in nodes.items() if node["output"]},
                "direct_output_table": {
                    node_id: list(node["direct_output"]) for node_id, node in nodes.items() if node["direct_output"]
                },
                "automaton_nodes": node_rows,
                "failure_trace": list(failure_trace),
                "scan_trace": list(scan_trace),
                "matches": list(matches),
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_NODE,
            target_type="node",
            target_id=root_id,
            value={"id": root_id, "label": "(root)"},
            message="Create Aho-Corasick root",
            phase="init",
            state=automaton_state({"phase_detail": "create root"}),
        )
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Build trie for patterns: {', '.join(patterns)}",
            phase="init",
            state=automaton_state({"phase_detail": "build trie"}),
        )

        for pattern in patterns:
            current = root_id
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Insert pattern '{pattern}'",
                phase="explore",
                state=automaton_state({"current_pattern": pattern, "current_node": current}),
            )
            for char in pattern:
                children = nodes[current]["children"]
                if char in children:
                    child = children[char]
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=f"{current}-{child}",
                        value="exploring",
                        message=f"Follow existing trie edge '{char}'",
                        phase="explore",
                        state=automaton_state({"current_pattern": pattern, "current_node": child}),
                    )
                else:
                    child = make_node(char, current, char)
                    children[char] = child
                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=child,
                        value={"id": child, "label": char},
                        message=f"Create trie node for '{char}'",
                        phase="explore",
                        state=automaton_state({"current_pattern": pattern, "current_node": child}),
                    )
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=f"{current}-{child}",
                        value={"source": current, "target": child, "label": char},
                        message=f"Add trie edge '{char}'",
                        phase="explore",
                        state=automaton_state({"current_pattern": pattern, "current_node": child}),
                    )
                current = child

            nodes[current]["direct_output"].append(pattern)
            nodes[current]["output"].append(pattern)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="path",
                message=f"Mark output '{pattern}' at node {current}",
                phase="finalize",
                state=automaton_state({"current_pattern": pattern, "output_node": current}),
            )

        queue: deque[str] = deque()
        for char, child in sorted(nodes[root_id]["children"].items()):
            nodes[child]["fail"] = root_id
            queue.append(child)
            failure_trace.append({"node": child, "char": char, "fail": root_id, "reason": "root child"})
            yield Step(
                action=StepAction.ADD_EDGE,
                target_type="edge",
                target_id=f"fail-{child}",
                value={"source": child, "target": root_id, "label": "fail", "dashes": True, "color": "#e74c3c"},
                message=f"Set fail({child}) to root",
                phase="init",
                state=automaton_state({"queue": list(queue), "failure_node": child}),
            )

        while queue:
            current = queue.popleft()
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Process failure transitions from node {current}",
                phase="explore",
                state=automaton_state({"queue": list(queue), "current_node": current}),
            )

            for char, child in sorted(nodes[current]["children"].items()):
                fallback = nodes[current]["fail"]
                followed: list[str] = []
                while fallback != root_id and char not in nodes[fallback]["children"]:
                    followed.append(fallback)
                    fallback = nodes[fallback]["fail"]
                if char in nodes[fallback]["children"]:
                    fail_target = nodes[fallback]["children"][char]
                else:
                    fail_target = root_id

                nodes[child]["fail"] = fail_target
                inherited = [pattern for pattern in nodes[fail_target]["output"] if pattern not in nodes[child]["output"]]
                nodes[child]["output"].extend(inherited)
                queue.append(child)
                failure_trace.append({
                    "node": child,
                    "char": char,
                    "from": current,
                    "fail": fail_target,
                    "followed": followed,
                    "inherited_output": inherited,
                })

                yield Step(
                    action=StepAction.ADD_EDGE,
                    target_type="edge",
                    target_id=f"fail-{child}",
                    value={"source": child, "target": fail_target, "label": "fail", "dashes": True, "color": "#e74c3c"},
                    message=f"Set fail({child}) to {fail_target}; inherit {inherited or 'no'} output",
                    phase="explore",
                    state=automaton_state({
                        "queue": list(queue),
                        "current_node": child,
                        "fail_target": fail_target,
                        "followed_failure_links": followed,
                    }),
                )

        if not text:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="Automaton built; no text provided for scanning",
                phase="result",
                state=automaton_state({"match_count": 0}),
            )
            return

        current = root_id
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Scan text '{text}'",
            phase="init",
            state=automaton_state({"current_node": current, "scan_index": 0}),
        )

        for index, char in enumerate(text):
            fallback_path: list[str] = []
            while current != root_id and char not in nodes[current]["children"]:
                old = current
                current = nodes[current]["fail"]
                fallback_path.append(old)
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=f"fail-{old}",
                    value="exploring",
                    message=f"No '{char}' transition; follow fail from {old} to {current}",
                    phase="explore",
                    state=automaton_state({
                        "scan_index": index,
                        "scan_char": char,
                        "current_node": current,
                        "fallback_path": list(fallback_path),
                    }),
                )

            transitioned = False
            if char in nodes[current]["children"]:
                previous = current
                current = nodes[current]["children"][char]
                transitioned = True
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=f"{previous}-{current}",
                    value="exploring",
                    message=f"Read '{char}' at {index}; transition to {current}",
                    phase="explore",
                    state=automaton_state({
                        "scan_index": index,
                        "scan_char": char,
                        "current_node": current,
                        "fallback_path": list(fallback_path),
                    }),
                )
            else:
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=root_id,
                    value="current",
                    message=f"Read '{char}' at {index}; stay at root",
                    phase="explore",
                    state=automaton_state({
                        "scan_index": index,
                        "scan_char": char,
                        "current_node": current,
                        "fallback_path": list(fallback_path),
                    }),
                )

            found_here: list[dict] = []
            for pattern in nodes[current]["output"]:
                start = index - len(pattern) + 1
                match = {"pattern": pattern, "start": start, "end": index, "node": current}
                matches.append(match)
                found_here.append(match)

            scan_entry = {
                "index": index,
                "char": char,
                "node": current,
                "transitioned": transitioned,
                "fallback_path": fallback_path,
                "outputs": list(nodes[current]["output"]),
                "matches": found_here,
            }
            scan_trace.append(scan_entry)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="path" if found_here else "current",
                message=(
                    f"Match at index {index}: {', '.join(match['pattern'] for match in found_here)}"
                    if found_here
                    else f"No output at index {index}"
                ),
                phase="finalize" if found_here else "explore",
                state=automaton_state({
                    "scan_index": index,
                    "scan_char": char,
                    "current_node": current,
                    "current_outputs": list(nodes[current]["output"]),
                    "matches_at_index": found_here,
                }),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Found {len(matches)} match(es)",
            phase="result",
            state=automaton_state({"match_count": len(matches)}),
        )

"""Aho-Corasick automaton — multi-pattern string matching."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class AhoCorasickAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="aho_corasick",
            category="tree",
            description="Aho-Corasick automaton for multi-pattern string matching — "
            "builds a trie with failure links and scans text in one pass",
            emoji="🔍",
            parameters=[
                {"name": "patterns", "type": "str", "required": True,
                 "description": "Comma-separated patterns (e.g. he,she,his,her)"},
                {"name": "text", "type": "str", "required": True,
                 "description": "Text to search (e.g. ashers)"},
            ],
            time_complexity="O(n + m + z) — n=total pattern chars, m=text length, z=matches",
            space_complexity="O(n * ALPHABET_SIZE)",
            layout="hierarchical",
            builds_structure=True,
            use_cases=[
                "Multi-pattern string matching",
                "Intrusion detection systems (IDS)",
                "Antivirus signature scanning",
                "Plagiarism detection",
                "DNA sequence matching",
            ],
            pseudocode=(
                "Phase 1 — Build Trie:\n"
                "  for each pattern:\n"
                "    insert chars into trie, mark end node\n"
                "\n"
                "Phase 2 — Build Failure Links (BFS):\n"
                "  queue = root's children\n"
                "  while queue not empty:\n"
                "    node = dequeue\n"
                "    for each (char, child) of node:\n"
                "      f = node.failure\n"
                "      while f != root and char not in f.children:\n"
                "        f = f.failure\n"
                "      child.failure = f.children[char] if exists else root\n"
                "      enqueue child\n"
                "\n"
                "Phase 3 — Search Text:\n"
                "  node = root\n"
                "  for each char in text:\n"
                "    while node != root and char not in node.children:\n"
                "      node = node.failure\n"
                "    if char in node.children: node = node.children[char]\n"
                "    if node is pattern end: report match"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        patterns_str = params.get("patterns", "")
        text = params.get("text", "").strip().lower()
        if not patterns_str:
            return

        patterns = [p.strip().lower() for p in patterns_str.split(",") if p.strip()]
        if not patterns:
            return

        # ---- internal trie structure ----
        # node: {"id", "char", "children": {char: nid}, "fail": nid|None, "output": [pattern]}
        nodes: dict[str, dict] = {}
        counter = 0

        def make_node(char: str) -> str:
            nonlocal counter
            counter += 1
            nid = f"ac{counter}"
            nodes[nid] = {"id": nid, "char": char, "children": {}, "fail": None, "output": [], "parent": None}
            return nid

        # ===================== Phase 1: Build Trie =====================
        root_id = make_node("*")
        nodes[root_id]["fail"] = root_id  # root's failure = root
        yield Step(
            action=StepAction.ADD_NODE,
            target_type="node",
            target_id=root_id,
            value={"id": root_id, "label": "(root)"},
            message="Created automaton root",
            phase="init",
        )
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Phase 1: Building trie from patterns: {', '.join(patterns)}",
            phase="init",
        )

        for pattern in patterns:
            cur = root_id
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=cur,
                value="current",
                message=f"Inserting pattern '{pattern}'",
                phase="explore",
            )
            for ch in pattern:
                children = nodes[cur]["children"]
                if ch in children:
                    nxt = children[ch]
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=f"{cur}-{nxt}",
                        value="exploring",
                        message=f"Follow existing edge '{ch}'",
                        phase="explore",
                    )
                else:
                    nxt = make_node(ch)
                    nodes[nxt]["parent"] = cur
                    nodes[cur]["children"][ch] = nxt
                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=nxt,
                        value={"id": nxt, "label": ch},
                        message=f"Create node for '{ch}'",
                        phase="explore",
                    )
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=f"{cur}-{nxt}",
                        value={"source": cur, "target": nxt, "label": ch},
                        message=f"Add trie edge '{ch}'",
                        phase="explore",
                    )
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=nxt,
                    value="current",
                    message=f"Move to '{ch}'",
                    phase="explore",
                )
                cur = nxt

            nodes[cur]["output"].append(pattern)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=cur,
                value="path",
                message=f"'{pattern}' complete — mark output",
                phase="finalize",
            )

        # ===================== Phase 2: Failure Links (BFS) =====================
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Phase 2: Building failure links via BFS",
            phase="init",
        )

        queue: deque[str] = deque()
        # Initialize: root's direct children fail to root
        for ch, child_id in nodes[root_id]["children"].items():
            nodes[child_id]["fail"] = root_id
            queue.append(child_id)
            yield Step(
                action=StepAction.ADD_EDGE,
                target_type="edge",
                target_id=f"fail-{child_id}",
                value={"source": child_id, "target": root_id, "label": "fail",
                        "dashes": True, "color": "#e74c3c"},
                message=f"fail('{nodes[child_id]['char']}') → root",
                phase="explore",
            )

        while queue:
            cur = queue.popleft()
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=cur,
                value="current",
                message=f"Computing failure links for children of '{nodes[cur]['char']}'",
                phase="explore",
            )

            for ch, child_id in nodes[cur]["children"].items():
                # Walk failure chain to find fallback
                f = nodes[cur]["fail"]
                while f != root_id and ch not in nodes[f]["children"]:
                    f = nodes[f]["fail"]
                if ch in nodes[f]["children"]:
                    fail_target = nodes[f]["children"][ch]
                else:
                    fail_target = root_id

                nodes[child_id]["fail"] = fail_target
                # Propagate output
                nodes[child_id]["output"] = (
                    nodes[child_id]["output"] + nodes[fail_target]["output"]
                )

                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=f"{cur}-{child_id}",
                    value="exploring",
                    message=f"Process child '{ch}'",
                    phase="explore",
                )

                if fail_target != root_id:
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=f"fail-{child_id}",
                        value={"source": child_id, "target": fail_target, "label": "fail",
                                "dashes": True, "color": "#e74c3c"},
                        message=f"fail('{ch}') → '{nodes[fail_target]['char']}'",
                        phase="explore",
                    )
                else:
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=f"fail-{child_id}",
                        value={"source": child_id, "target": root_id, "label": "fail",
                                "dashes": True, "color": "#e74c3c"},
                        message=f"fail('{ch}') → root",
                        phase="explore",
                    )

                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=child_id,
                    value="visited",
                    message=f"Failure link set for '{ch}'",
                    phase="explore",
                )
                queue.append(child_id)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=cur,
                value="visited",
                message=f"Done with '{nodes[cur]['char']}'",
                phase="explore",
            )

        # ===================== Phase 3: Search Text =====================
        if not text:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="No text provided — automaton construction complete.",
                phase="result",
            )
            return

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Phase 3: Searching text: '{text}'",
            phase="init",
        )

        cur = root_id
        matches: list[tuple[int, str]] = []  # (position, pattern)

        for pos, ch in enumerate(text):
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=cur,
                value="current",
                message=f"Read '{ch}' (position {pos})",
                phase="explore",
            )

            # Follow failure links until we find a transition or reach root
            while cur != root_id and ch not in nodes[cur]["children"]:
                old = cur
                cur = nodes[cur]["fail"]
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=old,
                    value="exploring",
                    message=f"Follow fail link from '{nodes[old]['char']}'",
                    phase="explore",
                )

            if ch in nodes[cur]["children"]:
                nxt = nodes[cur]["children"][ch]
                parent = nodes[nxt].get("parent")
                if parent is not None:
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=f"{parent}-{nxt}",
                        value="exploring",
                        message=f"Transition '{ch}' → '{nodes[nxt]['char']}'",
                        phase="explore",
                    )
                cur = nxt
            else:
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=cur,
                    value="current",
                    message=f"Stay at root (no transition for '{ch}')",
                    phase="explore",
                )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=cur,
                value="current",
                message=f"Now at node '{nodes[cur]['char']}'",
                phase="explore",
            )

            # Check for matches via output
            if nodes[cur]["output"]:
                for pattern in nodes[cur]["output"]:
                    matches.append((pos, pattern))
                    # Highlight the matched node
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=cur,
                        value="path",
                        message=f"MATCH found: '{pattern}' ending at position {pos}",
                        phase="finalize",
                    )

        # ===================== Results =====================
        # Reset all node colors to visited
        for nid in nodes:
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=nid,
                value="visited",
                message="",
                phase="result",
            )

        if matches:
            match_strs = [f"'{pat}' at pos {pos - len(pat) + 1}–{pos}" for pos, pat in matches]
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Found {len(matches)} match(es): {', '.join(match_strs)}",
                phase="result",
            )
        else:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="No matches found.",
                phase="result",
            )

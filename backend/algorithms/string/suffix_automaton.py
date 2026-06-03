"""Suffix automaton construction and substring statistics visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class SuffixAutomatonAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="suffix_automaton",
            category="string",
            description="Build a suffix automaton with suffix links, clone states, and substring statistics",
            emoji="SAM",
            parameters=[
                {"name": "text", "type": "str", "required": True, "description": "Text to index"},
                {
                    "name": "query",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "Optional substring query",
                },
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="graph",
            time_complexity="O(n)",
            space_complexity="O(n * alphabet)",
            use_cases=[
                "Substring existence queries",
                "Counting distinct substrings",
                "Longest repeated substring",
                "Online string indexing",
                "Text compression and sequence analysis",
            ],
            pseudocode=(
                "create root state\n"
                "for each character c in text:\n"
                "    cur = new state with len = last.len + 1\n"
                "    while p exists and p has no transition c:\n"
                "        add transition p --c--> cur; p = link[p]\n"
                "    if p does not exist: link[cur] = root\n"
                "    else if len[p] + 1 == len[q]: link[cur] = q\n"
                "    else:\n"
                "        clone q; redirect transitions to clone\n"
                "        link[q] = link[cur] = clone\n"
                "    last = cur"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = str(params.get("text", "") or "").strip()
        query = str(params.get("query", "") or "").strip()
        if not text:
            return

        states: list[dict] = []
        build_trace: list[dict] = []
        clone_trace: list[dict] = []
        link_updates: list[dict] = []
        transition_updates: list[dict] = []

        def new_state(length: int, first_pos: int, is_clone: bool = False) -> int:
            state_id = len(states)
            states.append(
                {
                    "id": state_id,
                    "length": length,
                    "link": -1,
                    "next": {},
                    "first_pos": first_pos,
                    "is_clone": is_clone,
                    "occurrences": 0,
                }
            )
            return state_id

        root = new_state(0, -1)
        states[root]["link"] = -1
        last = root

        def node_id(index: int) -> str:
            return f"sam{index}"

        def state_rows() -> dict[str, dict]:
            return {
                node_id(index): {
                    "length": state["length"],
                    "link": node_id(state["link"]) if state["link"] >= 0 else None,
                    "transitions": {char: node_id(target) for char, target in sorted(state["next"].items())},
                    "first_pos": state["first_pos"],
                    "is_clone": state["is_clone"],
                    "occurrences": state["occurrences"],
                }
                for index, state in enumerate(states)
            }

        def suffix_link_table() -> dict[str, str | None]:
            return {
                node_id(index): node_id(state["link"]) if state["link"] >= 0 else None
                for index, state in enumerate(states)
            }

        def transition_table() -> list[dict]:
            rows = []
            for index, state in enumerate(states):
                for char, target in sorted(state["next"].items()):
                    rows.append({"from": node_id(index), "char": char, "to": node_id(target)})
            return rows

        def distinct_substring_count() -> int:
            total = 0
            for index, state in enumerate(states):
                if index == root:
                    continue
                link = state["link"]
                link_length = states[link]["length"] if link >= 0 else 0
                total += state["length"] - link_length
            return total

        def state_payload(extra: dict | None = None) -> dict:
            payload = {
                "text": text,
                "query": query,
                "last_state": node_id(last),
                "state_count": len(states),
                "states": state_rows(),
                "suffix_links": suffix_link_table(),
                "transition_table": transition_table(),
                "build_trace": list(build_trace),
                "clone_trace": list(clone_trace),
                "link_updates": list(link_updates),
                "transition_updates": list(transition_updates),
                "distinct_substring_count": distinct_substring_count(),
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_NODE,
            target_type="node",
            target_id=node_id(root),
            value={"id": node_id(root), "label": "root", "x": -260, "y": 0},
            message="Create suffix automaton root",
            phase="init",
            state=state_payload({"current_state": node_id(root)}),
        )

        for pos, char in enumerate(text):
            previous_last = last
            cur = new_state(states[last]["length"] + 1, pos)
            states[cur]["occurrences"] = 1
            event = {
                "index": pos,
                "char": char,
                "new_state": node_id(cur),
                "previous_last": node_id(previous_last),
                "length": states[cur]["length"],
            }
            build_trace.append(event)

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=node_id(cur),
                value={
                    "id": node_id(cur),
                    "label": f"{node_id(cur)}\nlen={states[cur]['length']}",
                    "x": -180 + pos * 70,
                    "y": 90 if pos % 2 else -90,
                },
                message=f"Read '{char}' at index {pos}; create state {node_id(cur)}",
                phase="explore",
                state=state_payload({"current_char": char, "current_state": node_id(cur), "current_event": event}),
            )

            p = last
            while p >= 0 and char not in states[p]["next"]:
                states[p]["next"][char] = cur
                update = {"from": node_id(p), "char": char, "to": node_id(cur), "reason": "missing transition"}
                transition_updates.append(update)
                yield Step(
                    action=StepAction.ADD_EDGE,
                    target_type="edge",
                    target_id=f"{node_id(p)}-{node_id(cur)}",
                    value={"source": node_id(p), "target": node_id(cur), "label": char},
                    message=f"Add transition {node_id(p)} --{char}--> {node_id(cur)}",
                    phase="explore",
                    state=state_payload({"current_transition": update, "current_state": node_id(cur)}),
                )
                p = states[p]["link"]

            if p == -1:
                states[cur]["link"] = root
                update = {"state": node_id(cur), "from": None, "to": node_id(root), "reason": "reached root"}
                link_updates.append(update)
                yield Step(
                    action=StepAction.SET_NODE_BORDER,
                    target_type="node",
                    target_id=node_id(cur),
                    value={"width": 4, "color": "#34d399"},
                    message=f"Set suffix link {node_id(cur)} -> root",
                    phase="relax",
                    state=state_payload({"current_link_update": update}),
                )
            else:
                q = states[p]["next"][char]
                if states[p]["length"] + 1 == states[q]["length"]:
                    states[cur]["link"] = q
                    update = {"state": node_id(cur), "from": None, "to": node_id(q), "reason": "continuous transition"}
                    link_updates.append(update)
                    yield Step(
                        action=StepAction.SET_NODE_BORDER,
                        target_type="node",
                        target_id=node_id(cur),
                        value={"width": 4, "color": "#34d399"},
                        message=f"Set suffix link {node_id(cur)} -> {node_id(q)}",
                        phase="relax",
                        state=state_payload({"current_link_update": update}),
                    )
                else:
                    clone = new_state(states[p]["length"] + 1, states[q]["first_pos"], is_clone=True)
                    states[clone]["next"] = dict(states[q]["next"])
                    states[clone]["link"] = states[q]["link"]
                    clone_event = {
                        "clone": node_id(clone),
                        "source_state": node_id(q),
                        "length": states[clone]["length"],
                        "copied_transitions": {c: node_id(t) for c, t in sorted(states[clone]["next"].items())},
                        "suffix_link": node_id(states[clone]["link"]) if states[clone]["link"] >= 0 else None,
                    }
                    clone_trace.append(clone_event)

                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=node_id(clone),
                        value={
                            "id": node_id(clone),
                            "label": f"{node_id(clone)}\nclone len={states[clone]['length']}",
                            "x": -180 + pos * 70,
                            "y": 180,
                        },
                        message=f"Clone {node_id(q)} into {node_id(clone)}",
                        phase="relax",
                        state=state_payload({"current_clone": clone_event}),
                    )

                    while p >= 0 and states[p]["next"].get(char) == q:
                        states[p]["next"][char] = clone
                        update = {
                            "from": node_id(p),
                            "char": char,
                            "old_to": node_id(q),
                            "to": node_id(clone),
                            "reason": "redirect to clone",
                        }
                        transition_updates.append(update)
                        yield Step(
                            action=StepAction.ADD_MESSAGE,
                            target_type="node",
                            target_id=node_id(p),
                            message=f"Redirect {node_id(p)} --{char}--> {node_id(clone)}",
                            phase="relax",
                            state=state_payload({"current_transition": update, "current_clone": clone_event}),
                        )
                        p = states[p]["link"]

                    old_q_link = states[q]["link"]
                    states[q]["link"] = clone
                    states[cur]["link"] = clone
                    q_update = {
                        "state": node_id(q),
                        "from": node_id(old_q_link) if old_q_link >= 0 else None,
                        "to": node_id(clone),
                        "reason": "clone split",
                    }
                    cur_update = {"state": node_id(cur), "from": None, "to": node_id(clone), "reason": "clone split"}
                    link_updates.extend([q_update, cur_update])
                    yield Step(
                        action=StepAction.SET_NODE_BORDER,
                        target_type="node",
                        target_id=node_id(clone),
                        value={"width": 4, "color": "#fbbf24"},
                        message=f"Suffix links now point to clone {node_id(clone)}",
                        phase="relax",
                        state=state_payload({"current_link_update": cur_update, "current_clone": clone_event}),
                    )

            last = cur
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id(last),
                value="current",
                message=f"Set last = {node_id(last)}",
                phase="finalize",
                state=state_payload({"current_state": node_id(last), "processed_prefix": text[: pos + 1]}),
            )

        for index in sorted(range(len(states)), key=lambda item: states[item]["length"], reverse=True):
            link = states[index]["link"]
            if link >= 0:
                states[link]["occurrences"] += states[index]["occurrences"]

        longest_repeated = ""
        repeated_candidates: list[dict] = []
        for index, state in enumerate(states):
            if state["occurrences"] < 2 or state["length"] == 0:
                continue
            start = state["first_pos"] - state["length"] + 1
            substring = text[start: state["first_pos"] + 1]
            repeated_candidates.append({"state": node_id(index), "substring": substring, "length": state["length"], "occurrences": state["occurrences"]})
            if len(substring) > len(longest_repeated):
                longest_repeated = substring

        query_found = None
        query_path: list[str] = []
        if query:
            cursor = root
            query_found = True
            for char in query:
                if char not in states[cursor]["next"]:
                    query_found = False
                    break
                cursor = states[cursor]["next"][char]
                query_path.append(node_id(cursor))

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=(
                f"Suffix automaton complete: {len(states)} states, "
                f"{distinct_substring_count()} distinct substrings"
            ),
            phase="result",
            state=state_payload(
                {
                    "occurrence_table": {node_id(index): state["occurrences"] for index, state in enumerate(states)},
                    "longest_repeated_substring": longest_repeated,
                    "repeated_candidates": repeated_candidates,
                    "query_found": query_found,
                    "query_path": query_path,
                }
            ),
        )

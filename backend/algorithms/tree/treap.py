"""Treap - randomized balanced BST with heap priorities."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class TreapAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="treap",
            category="tree",
            description="Treap insertion with BST keys and heap priorities",
            emoji="TR",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated keys to insert"},
                {"name": "priorities", "type": "str", "required": False, "default": "", "description": "Optional comma-separated priorities; smaller rises higher"},
            ],
            time_complexity="Expected O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
            builds_structure=True,
            use_cases=[
                "Randomized balanced search trees",
                "Ordered maps and sets",
                "Split and merge tree operations",
                "Teaching BST plus heap invariants",
            ],
            pseudocode=(
                "function TreapInsert(root, key, priority):\n"
                "    insert by BST key\n"
                "    if child.priority < root.priority:\n"
                "        rotate child up\n"
                "    return root"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        values_raw = str(params.get("values", "")).strip()
        if not values_raw:
            return

        try:
            values = [int(item.strip()) for item in values_raw.split(",") if item.strip()]
        except ValueError:
            values = [item.strip() for item in values_raw.split(",") if item.strip()]
        if not values:
            return

        priority_raw = str(params.get("priorities", "")).strip()
        priorities: list[int] = []
        if priority_raw:
            try:
                priorities = [int(item.strip()) for item in priority_raw.split(",") if item.strip()]
            except ValueError:
                priorities = []
        if len(priorities) < len(values):
            # Deterministic fallback keeps examples and tests repeatable.
            priorities = priorities + [((idx + 1) * 37 + len(str(value)) * 11) % 97 + 1 for idx, value in enumerate(values[len(priorities):], start=len(priorities))]

        nodes: dict[str, dict] = {}
        root_id: str | None = None
        node_counter = 0
        rotations: list[dict] = []

        def make_id() -> str:
            nonlocal node_counter
            node_counter += 1
            return f"t{node_counter}"

        def label(nid: str) -> str:
            return f"{nodes[nid]['value']}|p{nodes[nid]['priority']}"

        def current_edges() -> list[tuple[str, str, str]]:
            result = []
            for nid, nd in nodes.items():
                if nd["left"]:
                    result.append((nid, nd["left"], "L"))
                if nd["right"]:
                    result.append((nid, nd["right"], "R"))
            return result

        def tree_state(extra: dict | None = None) -> dict:
            def walk(nid):
                if nid is None or nid not in nodes:
                    return None
                return {
                    "key": nodes[nid]["value"],
                    "priority": nodes[nid]["priority"],
                    "left": walk(nodes[nid]["left"]),
                    "right": walk(nodes[nid]["right"]),
                }

            def inorder(nid, result):
                if nid is None or nid not in nodes:
                    return
                inorder(nodes[nid]["left"], result)
                result.append(nodes[nid]["value"])
                inorder(nodes[nid]["right"], result)

            def heap_ok(nid) -> bool:
                if nid is None or nid not in nodes:
                    return True
                nd = nodes[nid]
                for child_id in [nd["left"], nd["right"]]:
                    if child_id and nodes[child_id]["priority"] < nd["priority"]:
                        return False
                return heap_ok(nd["left"]) and heap_ok(nd["right"])

            ordered = []
            inorder(root_id, ordered)
            payload = {
                "root": nodes[root_id]["value"] if root_id else None,
                "inorder": ordered,
                "heap_valid": heap_ok(root_id),
                "rotations": list(rotations),
                "tree": walk(root_id),
            }
            if extra:
                payload.update(extra)
            return payload

        def remove_edges(edges: list[tuple[str, str, str]]) -> Generator[Step, None, None]:
            for parent_id, child_id, _ in edges:
                yield Step(
                    action=StepAction.REMOVE_EDGE,
                    target_type="edge",
                    target_id=f"{parent_id}-{child_id}",
                    message="Remove stale Treap edge",
                    phase="relax",
                )

        def add_edges() -> Generator[Step, None, None]:
            for parent_id, child_id, side in current_edges():
                yield Step(
                    action=StepAction.ADD_EDGE,
                    target_type="edge",
                    target_id=f"{parent_id}-{child_id}",
                    value={"source": parent_id, "target": child_id, "label": side},
                    message=f"Add {side} edge {parent_id} -> {child_id}",
                    phase="relax",
                )

        def rotate_right(nid: str) -> str:
            left_id = nodes[nid]["left"]
            nodes[nid]["left"] = nodes[left_id]["right"]
            nodes[left_id]["right"] = nid
            rotations.append({"type": "right", "at": nodes[nid]["value"], "promoted": nodes[left_id]["value"]})
            return left_id

        def rotate_left(nid: str) -> str:
            right_id = nodes[nid]["right"]
            nodes[nid]["right"] = nodes[right_id]["left"]
            nodes[right_id]["left"] = nid
            rotations.append({"type": "left", "at": nodes[nid]["value"], "promoted": nodes[right_id]["value"]})
            return right_id

        def insert(nid: str | None, new_id: str) -> Generator[Step, None, str]:
            if nid is None:
                return new_id

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=nid,
                value="current",
                message=f"Compare key {nodes[new_id]['value']} with {nodes[nid]['value']}",
                phase="explore",
                state=tree_state({"insert_key": nodes[new_id]["value"]}),
            )

            if nodes[new_id]["value"] < nodes[nid]["value"]:
                old_edges = current_edges()
                nodes[nid]["left"] = yield from insert(nodes[nid]["left"], new_id)
                if nodes[nodes[nid]["left"]]["priority"] < nodes[nid]["priority"]:
                    yield from remove_edges(old_edges)
                    nid = rotate_right(nid)
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="node",
                        target_id="",
                        message=f"Right rotate because left child priority is smaller",
                        phase="relax",
                        state=tree_state({"rotation": rotations[-1]}),
                    )
                    yield from add_edges()
            else:
                old_edges = current_edges()
                nodes[nid]["right"] = yield from insert(nodes[nid]["right"], new_id)
                if nodes[nodes[nid]["right"]]["priority"] < nodes[nid]["priority"]:
                    yield from remove_edges(old_edges)
                    nid = rotate_left(nid)
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="node",
                        target_id="",
                        message=f"Left rotate because right child priority is smaller",
                        phase="relax",
                        state=tree_state({"rotation": rotations[-1]}),
                    )
                    yield from add_edges()

            return nid

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Building Treap from: {values_raw}",
            phase="init",
        )

        for value, priority in zip(values, priorities):
            new_id = make_id()
            nodes[new_id] = {"value": value, "priority": priority, "left": None, "right": None}
            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=new_id,
                value={"id": new_id, "label": label(new_id)},
                message=f"Insert key {value} with priority {priority}",
                phase="explore",
                state=tree_state({"insert_key": value, "insert_priority": priority}),
            )
            old_edges = current_edges()
            root_id = yield from insert(root_id, new_id)
            yield from remove_edges(old_edges)
            yield from add_edges()
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=new_id,
                value="visited",
                message=f"Treap invariants restored after inserting {value}",
                phase="finalize",
                state=tree_state({"inserted_key": value}),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Treap complete. {len(values)} nodes, {len(rotations)} rotation(s).",
            phase="result",
            state=tree_state(),
        )

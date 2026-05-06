"""Binary Search Tree - insert and search."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BSTAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="bst",
            category="tree",
            description="Binary Search Tree with insert and search operations",
            emoji="🔍",
            parameters=[
                {"name": "values", "type": "str", "required": True,
                 "description": "Comma-separated values to insert (e.g. 50,30,70,20,40)"},
            ],
            time_complexity="O(n log n) avg, O(n) worst",
            space_complexity="O(n)",
            layout="hierarchical",
            use_cases=[
                "Efficient lookup, insert, delete",
                "In-order traversal gives sorted sequence",
                "Database indexing",
                "Symbol tables",
                "Priority queues",
            ],
            pseudocode=(
                "function BST_Insert(root, value):\n"
                "    if root is null:\n"
                "        return new Node(value)\n"
                "    if value < root.value:\n"
                "        root.left = BST_Insert(root.left, value)\n"
                "    else:\n"
                "        root.right = BST_Insert(root.right, value)\n"
                "    return root"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        values_str = params.get("values", "")
        if not values_str:
            return

        try:
            values = [int(v.strip()) for v in values_str.split(",") if v.strip()]
        except ValueError:
            values = [v.strip() for v in values_str.split(",") if v.strip()]

        if not values:
            return

        # Internal BST structure: {id: {"left": id|None, "right": id|None, "value": any}}
        tree: dict[str, dict] = {}
        root_id = None
        node_counter = 0

        def make_node_id(val):
            nonlocal node_counter
            node_counter += 1
            return f"n{node_counter}"

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Building BST from values: {values_str}",
            phase="init",
        )

        for val in values:
            node_id = make_node_id(val)

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=node_id,
                value={"id": node_id, "label": str(val)},
                message=f"Inserting {val}",
                phase="explore",
            )

            if root_id is None:
                root_id = node_id
                tree[node_id] = {"left": None, "right": None, "value": val}
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=node_id,
                    value="current",
                    message=f"{val} is the root",
                    phase="explore",
                )
            else:
                # Find insertion point
                current = root_id
                while True:
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=current,
                        value="current",
                        message=f"Comparing {val} with {tree[current]['value']}",
                        phase="explore",
                    )

                    if val < tree[current]["value"]:
                        if tree[current]["left"] is None:
                            tree[current]["left"] = node_id
                            tree[node_id] = {"left": None, "right": None, "value": val}
                            yield Step(
                                action=StepAction.ADD_EDGE,
                                target_type="edge",
                                target_id=f"{current}-{node_id}",
                                value={"source": current, "target": node_id, "label": "L"},
                                message=f"{val} inserted as left child of {tree[current]['value']}",
                                phase="explore",
                            )
                            break
                        else:
                            yield Step(
                                action=StepAction.SET_NODE_COLOR,
                                target_type="node",
                                target_id=current,
                                value="visited",
                                message=f"{val} < {tree[current]['value']}, go left",
                                phase="explore",
                            )
                            current = tree[current]["left"]
                    else:
                        if tree[current]["right"] is None:
                            tree[current]["right"] = node_id
                            tree[node_id] = {"left": None, "right": None, "value": val}
                            yield Step(
                                action=StepAction.ADD_EDGE,
                                target_type="edge",
                                target_id=f"{current}-{node_id}",
                                value={"source": current, "target": node_id, "label": "R"},
                                message=f"{val} inserted as right child of {tree[current]['value']}",
                                phase="explore",
                            )
                            break
                        else:
                            yield Step(
                                action=StepAction.SET_NODE_COLOR,
                                target_type="node",
                                target_id=current,
                                value="visited",
                                message=f"{val} >= {tree[current]['value']}, go right",
                                phase="explore",
                            )
                            current = tree[current]["right"]

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="visited",
                message=f"{val} inserted successfully",
                phase="finalize",
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"BST construction complete. {len(values)} nodes inserted.",
            phase="result",
        )

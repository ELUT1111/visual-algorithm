"""B-Tree insert with node splitting."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BTreeAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="btree",
            category="tree",
            description="B-Tree insert with node splitting visualization",
            emoji="🌳",
            parameters=[
                {"name": "values", "type": "str", "required": True,
                 "description": "Comma-separated values to insert (e.g. 10,20,5,15,25,30)"},
                {"name": "order", "type": "str", "required": False, "default": "3",
                 "description": "B-Tree order (max children per node, default 3)"},
            ],
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
            use_cases=[
                "Database indexing (MySQL, PostgreSQL)",
                "File systems (NTFS, HFS+)",
                "Large dataset storage",
                "External memory algorithms",
                "When data doesn't fit in RAM",
            ],
            pseudocode=(
                "function BTree_Insert(root, value):\n"
                "    if root is full:\n"
                "        split root, create new root\n"
                "    insert_non_full(root, value)\n"
                "\n"
                "function insert_non_full(node, value):\n"
                "    if node is leaf:\n"
                "        insert value in sorted position\n"
                "    else:\n"
                "        find child to descend\n"
                "        if child is full:\n"
                "            split child\n"
                "        insert_non_full(child, value)"
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

        order_str = params.get("order", "3")
        try:
            order = max(3, int(order_str))
        except ValueError:
            order = 3

        if not values:
            return

        t = (order + 1) // 2  # minimum degree
        node_counter = 0
        btree_nodes: dict[str, dict] = {}  # id -> {"keys": [], "children": [], "leaf": bool}
        root_id = None

        def make_id():
            nonlocal node_counter
            node_counter += 1
            return f"b{node_counter}"

        def rebuild_all_edges():
            """Remove all edges and re-add them."""
            for nid, nd in btree_nodes.items():
                for child_id in nd["children"]:
                    if child_id:
                        yield Step(
                            action=StepAction.REMOVE_EDGE,
                            target_type="edge",
                            target_id=f"{nid}-{child_id}",
                            value=None,
                            message="",
                            phase="relax",
                        )
            for nid, nd in btree_nodes.items():
                for child_id in nd["children"]:
                    if child_id and child_id in btree_nodes:
                        yield Step(
                            action=StepAction.ADD_EDGE,
                            target_type="edge",
                            target_id=f"{nid}-{child_id}",
                            value={"source": nid, "target": child_id, "label": ""},
                            message="",
                            phase="relax",
                        )

        def update_node_display(nid):
            """Update node label to show keys."""
            if nid not in btree_nodes:
                return
            keys = btree_nodes[nid]["keys"]
            label = "|".join(str(k) for k in keys)
            yield Step(
                action=StepAction.UPDATE_NODE_LABEL,
                target_type="node",
                target_id=nid,
                value=label,
                message=f"Node keys: [{', '.join(str(k) for k in keys)}]",
                phase="relax",
            )

        def split_child(parent_id, i):
            nonlocal root_id
            parent = btree_nodes[parent_id]
            child_id = parent["children"][i]
            child = btree_nodes[child_id]

            new_id = make_id()
            new_node = {"keys": child["keys"][t:], "children": child["children"][t:] if not child["leaf"] else [], "leaf": child["leaf"]}
            btree_nodes[new_id] = new_node

            median = child["keys"][t - 1]
            child["keys"] = child["keys"][:t - 1]
            child["children"] = child["children"][:t] if not child["leaf"] else []

            parent["children"].insert(i + 1, new_id)
            parent["keys"].insert(i, median)

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=new_id,
                value={"id": new_id, "label": "|".join(str(k) for k in new_node["keys"])},
                message=f"Split: create new node with keys [{', '.join(str(k) for k in new_node['keys'])}]",
                phase="explore",
            )

            yield from update_node_display(child_id)
            yield from update_node_display(parent_id)
            yield from rebuild_all_edges()

        def insert_non_full(node_id, val):
            nonlocal root_id
            node = btree_nodes[node_id]
            i = len(node["keys"]) - 1

            if node["leaf"]:
                node["keys"].append(None)
                while i >= 0 and node["keys"][i] > val:
                    node["keys"][i + 1] = node["keys"][i]
                    i -= 1
                node["keys"][i + 1] = val

                yield from update_node_display(node_id)
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=node_id,
                    value="current",
                    message=f"Inserted {val} into leaf node",
                    phase="explore",
                )
            else:
                while i >= 0 and node["keys"][i] > val:
                    i -= 1
                i += 1

                child_id = node["children"][i]
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=node_id,
                    value="exploring",
                    message=f"Descend to child {i} for value {val}",
                    phase="explore",
                )

                if len(btree_nodes[child_id]["keys"]) == 2 * t - 1:
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="node",
                        target_id=child_id,
                        message=f"Child is full, splitting before inserting {val}",
                        phase="relax",
                    )
                    yield from split_child(node_id, i)

                    if val > node["keys"][i]:
                        i += 1

                yield from insert_non_full(node["children"][i], val)

        def btree_insert(val):
            nonlocal root_id

            if root_id is None:
                root_id = make_id()
                btree_nodes[root_id] = {"keys": [val], "children": [], "leaf": True}
                yield Step(
                    action=StepAction.ADD_NODE,
                    target_type="node",
                    target_id=root_id,
                    value={"id": root_id, "label": str(val)},
                    message=f"Create root with key {val}",
                    phase="init",
                )
                return

            root = btree_nodes[root_id]
            if len(root["keys"]) == 2 * t - 1:
                new_root_id = make_id()
                btree_nodes[new_root_id] = {"keys": [], "children": [root_id], "leaf": False}

                yield Step(
                    action=StepAction.ADD_NODE,
                    target_type="node",
                    target_id=new_root_id,
                    value={"id": new_root_id, "label": ""},
                    message=f"Root full, create new root",
                    phase="relax",
                )

                yield from split_child(new_root_id, 0)
                root_id = new_root_id
                yield from insert_non_full(new_root_id, val)
            else:
                yield from insert_non_full(root_id, val)

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Building B-Tree (order {order}) from: {values_str}",
            phase="init",
        )

        for val in values:
            yield from btree_insert(val)

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"B-Tree complete. {len(values)} keys inserted.",
            phase="result",
        )

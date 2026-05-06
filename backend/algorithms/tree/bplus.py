"""B+ Tree insert with leaf-level linking."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BPlusTreeAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="bplus",
            category="tree",
            description="B+ Tree insert with leaf linking for range queries",
            emoji="🍃",
            parameters=[
                {"name": "values", "type": "str", "required": True,
                 "description": "Comma-separated values to insert (e.g. 10,20,5,15,25,30)"},
                {"name": "order", "type": "str", "required": False, "default": "3",
                 "description": "B+ Tree order (max keys per node, default 3)"},
            ],
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
            use_cases=[
                "Database systems (MySQL InnoDB)",
                "File systems",
                "Range queries efficiently",
                "Sequential access patterns",
                "When data must be stored in leaves",
            ],
            pseudocode=(
                "function BPlus_Insert(root, value):\n"
                "    find leaf node for value\n"
                "    if leaf has space:\n"
                "        insert in sorted order\n"
                "    else:\n"
                "        split leaf\n"
                "        promote median key to parent\n"
                "        if parent is full:\n"
                "            split parent recursively"
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

        max_keys = order - 1
        node_counter = 0
        bplus_nodes: dict[str, dict] = {}
        root_id = None
        leaf_links: list[tuple[str, str]] = []  # (from_id, to_id) for leaf chain

        def make_id():
            nonlocal node_counter
            node_counter += 1
            return f"bp{node_counter}"

        def rebuild_all_edges():
            for nid, nd in bplus_nodes.items():
                for child_id in nd.get("children", []):
                    if child_id:
                        yield Step(
                            action=StepAction.REMOVE_EDGE,
                            target_type="edge",
                            target_id=f"{nid}-{child_id}",
                            value=None, message="", phase="relax",
                        )
                # Remove leaf link edges
                for link_from, link_to in leaf_links:
                    yield Step(
                        action=StepAction.REMOVE_EDGE,
                        target_type="edge",
                        target_id=f"link-{link_from}-{link_to}",
                        value=None, message="", phase="relax",
                    )

            for nid, nd in bplus_nodes.items():
                for child_id in nd.get("children", []):
                    if child_id and child_id in bplus_nodes:
                        yield Step(
                            action=StepAction.ADD_EDGE,
                            target_type="edge",
                            target_id=f"{nid}-{child_id}",
                            value={"source": nid, "target": child_id, "label": ""},
                            message="", phase="relax",
                        )

            # Re-add leaf links with a different style
            for link_from, link_to in leaf_links:
                if link_from in bplus_nodes and link_to in bplus_nodes:
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=f"link-{link_from}-{link_to}",
                        value={"source": link_from, "target": link_to, "label": "->"},
                        message="Leaf link", phase="relax",
                    )

        def update_node_display(nid):
            if nid not in bplus_nodes:
                return
            keys = bplus_nodes[nid]["keys"]
            label = "|".join(str(k) for k in keys)
            if bplus_nodes[nid].get("leaf"):
                label = f"[{label}]"
            yield Step(
                action=StepAction.UPDATE_NODE_LABEL,
                target_type="node",
                target_id=nid,
                value=label,
                message=f"Node keys: [{', '.join(str(k) for k in keys)}]",
                phase="relax",
            )

        def get_leaves_in_order():
            """Get all leaf nodes in left-to-right order."""
            if root_id is None:
                return []
            leaves = []
            def find_leaves(nid):
                if nid not in bplus_nodes:
                    return
                if bplus_nodes[nid].get("leaf"):
                    leaves.append(nid)
                else:
                    for child_id in bplus_nodes[nid].get("children", []):
                        find_leaves(child_id)
            find_leaves(root_id)
            return leaves

        def rebuild_leaf_links():
            nonlocal leaf_links
            leaf_links = []
            leaves = get_leaves_in_order()
            for i in range(len(leaves) - 1):
                leaf_links.append((leaves[i], leaves[i + 1]))

        def split_leaf(parent_id, child_idx):
            nonlocal root_id
            parent = bplus_nodes[parent_id]
            leaf_id = parent["children"][child_idx]
            leaf = bplus_nodes[leaf_id]

            mid = len(leaf["keys"]) // 2
            new_id = make_id()
            new_leaf = {"keys": leaf["keys"][mid:], "children": [], "leaf": True}
            bplus_nodes[new_id] = new_leaf
            leaf["keys"] = leaf["keys"][:mid]

            # Promote the first key of new leaf (copy, not move)
            promote_key = new_leaf["keys"][0]

            parent["keys"].insert(child_idx, promote_key)
            parent["children"].insert(child_idx + 1, new_id)

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=new_id,
                value={"id": new_id, "label": f"[{'|'.join(str(k) for k in new_leaf['keys'])}]"},
                message=f"Split leaf: new node with [{', '.join(str(k) for k in new_leaf['keys'])}]",
                phase="explore",
            )

            yield from update_node_display(leaf_id)
            yield from update_node_display(parent_id)
            rebuild_leaf_links()
            yield from rebuild_all_edges()

        def split_internal(parent_id, child_idx):
            nonlocal root_id
            parent = bplus_nodes[parent_id]
            node_id = parent["children"][child_idx]
            node = bplus_nodes[node_id]

            mid = len(node["keys"]) // 2
            promote_key = node["keys"][mid]

            new_id = make_id()
            new_node = {"keys": node["keys"][mid + 1:], "children": node["children"][mid + 1:], "leaf": False}
            bplus_nodes[new_id] = new_node

            node["keys"] = node["keys"][:mid]
            node["children"] = node["children"][:mid + 1]

            parent["keys"].insert(child_idx, promote_key)
            parent["children"].insert(child_idx + 1, new_id)

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=new_id,
                value={"id": new_id, "label": "|".join(str(k) for k in new_node["keys"])},
                message=f"Split internal: promote {promote_key}",
                phase="explore",
            )

            yield from update_node_display(node_id)
            yield from update_node_display(parent_id)
            yield from rebuild_all_edges()

        def insert(node_id, val):
            nonlocal root_id
            node = bplus_nodes[node_id]

            if node.get("leaf"):
                # Insert into leaf
                i = 0
                while i < len(node["keys"]) and node["keys"][i] < val:
                    i += 1
                node["keys"].insert(i, val)

                yield from update_node_display(node_id)
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=node_id,
                    value="current",
                    message=f"Inserted {val} into leaf",
                    phase="explore",
                )

                if len(node["keys"]) > max_keys:
                    return True  # needs split
                return False
            else:
                # Find child to descend
                i = 0
                while i < len(node["keys"]) and val >= node["keys"][i]:
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

                needs_split = yield from insert(child_id, val)

                if needs_split:
                    if bplus_nodes[child_id].get("leaf"):
                        yield from split_leaf(node_id, i)
                    else:
                        yield from split_internal(node_id, i)

                    if len(node["keys"]) > max_keys:
                        return True
                return False

        def bplus_insert(val):
            nonlocal root_id

            if root_id is None:
                root_id = make_id()
                bplus_nodes[root_id] = {"keys": [val], "children": [], "leaf": True}
                yield Step(
                    action=StepAction.ADD_NODE,
                    target_type="node",
                    target_id=root_id,
                    value={"id": root_id, "label": f"[{val}]"},
                    message=f"Create root leaf with key {val}",
                    phase="init",
                )
                rebuild_leaf_links()
                return

            needs_split = yield from insert(root_id, val)

            if needs_split:
                # Root needs splitting
                old_root = bplus_nodes[root_id]
                if old_root.get("leaf"):
                    mid = len(old_root["keys"]) // 2
                    new_id = make_id()
                    new_leaf = {"keys": old_root["keys"][mid:], "children": [], "leaf": True}
                    bplus_nodes[new_id] = new_leaf
                    old_root["keys"] = old_root["keys"][:mid]

                    new_root_id = make_id()
                    bplus_nodes[new_root_id] = {"keys": [new_leaf["keys"][0]], "children": [root_id, new_id], "leaf": False}

                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=new_id,
                        value={"id": new_id, "label": f"[{'|'.join(str(k) for k in new_leaf['keys'])}]"},
                        message=f"Split root leaf",
                        phase="relax",
                    )
                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=new_root_id,
                        value={"id": new_root_id, "label": str(new_leaf["keys"][0])},
                        message=f"New root with key {new_leaf['keys'][0]}",
                        phase="relax",
                    )

                    root_id = new_root_id
                    yield from update_node_display(old_root["keys"] and root_id)
                else:
                    old_keys = old_root["keys"]
                    mid = len(old_keys) // 2
                    promote = old_keys[mid]

                    new_id = make_id()
                    new_node = {"keys": old_keys[mid + 1:], "children": old_root["children"][mid + 1:], "leaf": False}
                    bplus_nodes[new_id] = new_node
                    old_root["keys"] = old_keys[:mid]
                    old_root["children"] = old_root["children"][:mid + 1]

                    new_root_id = make_id()
                    bplus_nodes[new_root_id] = {"keys": [promote], "children": [root_id, new_id], "leaf": False}

                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=new_id,
                        value={"id": new_id, "label": "|".join(str(k) for k in new_node["keys"])},
                        message=f"Split root internal",
                        phase="relax",
                    )
                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=new_root_id,
                        value={"id": new_root_id, "label": str(promote)},
                        message=f"New root with key {promote}",
                        phase="relax",
                    )

                    root_id = new_root_id

            rebuild_leaf_links()
            yield from rebuild_all_edges()

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Building B+ Tree (order {order}) from: {values_str}",
            phase="init",
        )

        for val in values:
            yield from bplus_insert(val)

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"B+ Tree complete. {len(values)} keys inserted.",
            phase="result",
        )

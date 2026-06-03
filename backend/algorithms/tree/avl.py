"""AVL Tree - self-balancing BST with rotation visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class AVLAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="avl",
            category="tree",
            description="AVL tree with insert and automatic balancing via rotations",
            emoji="⚖️",
            parameters=[
                {"name": "values", "type": "str", "required": True,
                 "description": "Comma-separated values to insert (e.g. 50,30,70,20,40,10)"},
                {"name": "delete_values", "type": "str", "required": False, "default": "",
                 "description": "Optional comma-separated values to delete after insertion"},
            ],
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
            builds_structure=True,
            use_cases=[
                "Guaranteed O(log n) operations",
                "Database indexing with frequent lookups",
                "In-memory sorted data structures",
                "When worst-case performance matters",
                "Balanced binary search trees",
            ],
            pseudocode=(
                "function AVL_Insert(node, value):\n"
                "    if node is null: return new Node(value)\n"
                "    if value < node.value:\n"
                "        node.left = AVL_Insert(node.left, value)\n"
                "    else:\n"
                "        node.right = AVL_Insert(node.right, value)\n"
                "    update_height(node)\n"
                "    balance = get_balance(node)\n"
                "    if balance > 1 and value < node.left.value:\n"
                "        return rotate_right(node)  // LL\n"
                "    if balance < -1 and value > node.right.value:\n"
                "        return rotate_left(node)   // RR\n"
                "    if balance > 1 and value > node.left.value:\n"
                "        node.left = rotate_left(node.left)\n"
                "        return rotate_right(node)  // LR\n"
                "    if balance < -1 and value < node.right.value:\n"
                "        node.right = rotate_right(node.right)\n"
                "        return rotate_left(node)   // RL\n"
                "    return node\n"
                "\n"
                "function AVL_Delete(node, value):\n"
                "    delete as in BST\n"
                "    update_height(node)\n"
                "    rebalance with the same AVL rotations"
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

        # Internal AVL structure
        nodes: dict[str, dict] = {}  # id -> {"value", "left", "right", "height"}
        node_counter = 0
        root_id = None
        # Maps value to node_id for edge reconstruction
        parent_map: dict[str, str] = {}  # child_id -> parent_id

        def make_id(val):
            nonlocal node_counter
            node_counter += 1
            return f"a{node_counter}"

        def height(nid):
            if nid is None or nid not in nodes:
                return 0
            return nodes[nid].get("height", 1)

        def update_height(nid):
            if nid and nid in nodes:
                nodes[nid]["height"] = 1 + max(height(nodes[nid]["left"]), height(nodes[nid]["right"]))

        def balance_factor(nid):
            if nid is None or nid not in nodes:
                return 0
            return height(nodes[nid]["left"]) - height(nodes[nid]["right"])

        def remove_edges(nid):
            """Remove all edges from/to this node for re-rendering."""
            if nid in parent_map:
                parent = parent_map[nid]
                yield Step(
                    action=StepAction.REMOVE_EDGE,
                    target_type="edge",
                    target_id=f"{parent}-{nid}",
                    value=None,
                    message=f"Remove edge {parent} -> {nid}",
                    phase="relax",
                )

        def add_tree_edges(nid):
            """Re-add edges from this node to its children."""
            if nid is None or nid not in nodes:
                return
            for child_id in [nodes[nid]["left"], nodes[nid]["right"]]:
                if child_id and child_id in nodes:
                    parent_map[child_id] = nid
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=f"{nid}-{child_id}",
                        value={"source": nid, "target": child_id, "label": ""},
                        message=f"Add edge {nid} -> {child_id}",
                        phase="relax",
                    )

        def rebuild_subtree_edges(nid):
            """Remove and re-add all edges in subtree."""
            if nid is None or nid not in nodes:
                return
            yield from remove_edges(nid)
            for child_id in [nodes[nid]["left"], nodes[nid]["right"]]:
                if child_id:
                    yield from remove_edges(child_id)
            yield from add_tree_edges(nid)
            for child_id in [nodes[nid]["left"], nodes[nid]["right"]]:
                if child_id:
                    yield from add_tree_edges(child_id)

        def insert(nid, val):
            nonlocal root_id

            if nid is None:
                new_id = make_id(val)
                nodes[new_id] = {"value": val, "left": None, "right": None, "height": 1}

                yield Step(
                    action=StepAction.ADD_NODE,
                    target_type="node",
                    target_id=new_id,
                    value={"id": new_id, "label": str(val)},
                    message=f"Insert {val}",
                    phase="explore",
                )
                return new_id

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=nid,
                value="current",
                message=f"Compare {val} with {nodes[nid]['value']}",
                phase="explore",
            )

            if val < nodes[nid]["value"]:
                result_id = yield from insert(nodes[nid]["left"], val)
                nodes[nid]["left"] = result_id
                parent_map[result_id] = nid
                edge_id = f"{nid}-{result_id}"
                # Only add edge if not already present
                yield Step(
                    action=StepAction.ADD_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value={"source": nid, "target": result_id, "label": ""},
                    message=f"Edge {nid} -> {result_id}",
                    phase="explore",
                )
            else:
                result_id = yield from insert(nodes[nid]["right"], val)
                nodes[nid]["right"] = result_id
                parent_map[result_id] = nid
                edge_id = f"{nid}-{result_id}"
                yield Step(
                    action=StepAction.ADD_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value={"source": nid, "target": result_id, "label": ""},
                    message=f"Edge {nid} -> {result_id}",
                    phase="explore",
                )

            update_height(nid)
            bf = balance_factor(nid)

            # Update label to show balance factor
            yield Step(
                action=StepAction.UPDATE_NODE_LABEL,
                target_type="node",
                target_id=nid,
                value=f"{nodes[nid]['value']}({bf:+d})",
                message=f"Node {nodes[nid]['value']} balance: {bf:+d}",
                phase="relax",
            )

            # LL rotation
            if bf > 1 and val < nodes[nodes[nid]["left"]]["value"]:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id=nid,
                    message=f"LL imbalance at {nodes[nid]['value']}, right rotation",
                    phase="relax",
                )
                # Right rotation
                left_id = nodes[nid]["left"]
                yield from rebuild_subtree_edges(nid)

                nodes[nid]["left"] = nodes[left_id]["right"]
                nodes[left_id]["right"] = nid
                update_height(nid)
                update_height(left_id)

                if nid == root_id:
                    root_id = left_id

                yield from rebuild_subtree_edges(left_id)
                return left_id

            # RR rotation
            if bf < -1 and val > nodes[nodes[nid]["right"]]["value"]:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id=nid,
                    message=f"RR imbalance at {nodes[nid]['value']}, left rotation",
                    phase="relax",
                )
                right_id = nodes[nid]["right"]
                yield from rebuild_subtree_edges(nid)

                nodes[nid]["right"] = nodes[right_id]["left"]
                nodes[right_id]["left"] = nid
                update_height(nid)
                update_height(right_id)

                if nid == root_id:
                    root_id = right_id

                yield from rebuild_subtree_edges(right_id)
                return right_id

            # LR rotation
            if bf > 1 and val > nodes[nodes[nid]["left"]]["value"]:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id=nid,
                    message=f"LR imbalance at {nodes[nid]['value']}, left-right rotation",
                    phase="relax",
                )
                left_id = nodes[nid]["left"]
                yield from rebuild_subtree_edges(nid)

                # Left rotate left child
                left_right_id = nodes[left_id]["right"]
                nodes[left_id]["right"] = nodes[left_right_id]["left"]
                nodes[left_right_id]["left"] = left_id
                update_height(left_id)
                update_height(left_right_id)
                nodes[nid]["left"] = left_right_id

                # Right rotate root
                nodes[nid]["left"] = nodes[left_right_id]["right"]
                nodes[left_right_id]["right"] = nid
                update_height(nid)
                update_height(left_right_id)

                if nid == root_id:
                    root_id = left_right_id

                yield from rebuild_subtree_edges(left_right_id)
                return left_right_id

            # RL rotation
            if bf < -1 and val < nodes[nodes[nid]["right"]]["value"]:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id=nid,
                    message=f"RL imbalance at {nodes[nid]['value']}, right-left rotation",
                    phase="relax",
                )
                right_id = nodes[nid]["right"]
                yield from rebuild_subtree_edges(nid)

                # Right rotate right child
                right_left_id = nodes[right_id]["left"]
                nodes[right_id]["left"] = nodes[right_left_id]["right"]
                nodes[right_left_id]["right"] = right_id
                update_height(right_id)
                update_height(right_left_id)
                nodes[nid]["right"] = right_left_id

                # Left rotate root
                nodes[nid]["right"] = nodes[right_left_id]["left"]
                nodes[right_left_id]["left"] = nid
                update_height(nid)
                update_height(right_left_id)

                if nid == root_id:
                    root_id = right_left_id

                yield from rebuild_subtree_edges(right_left_id)
                return right_left_id

            return nid

        def tree_state(extra: dict | None = None) -> dict:
            def walk(nid):
                if nid is None or nid not in nodes:
                    return None
                return {
                    "id": nid,
                    "value": nodes[nid]["value"],
                    "height": nodes[nid]["height"],
                    "balance": balance_factor(nid),
                    "left": walk(nodes[nid]["left"]),
                    "right": walk(nodes[nid]["right"]),
                }

            def inorder(nid, result):
                if nid is None or nid not in nodes:
                    return
                inorder(nodes[nid]["left"], result)
                result.append(nodes[nid]["value"])
                inorder(nodes[nid]["right"], result)

            ordered = []
            inorder(root_id, ordered)
            payload = {
                "root": nodes[root_id]["value"] if root_id and root_id in nodes else None,
                "inorder": ordered,
                "height": height(root_id),
                "tree": walk(root_id),
            }
            if extra:
                payload.update(extra)
            return payload

        def min_node(nid):
            current = nid
            while current and nodes[current]["left"]:
                current = nodes[current]["left"]
            return current

        def rotate_right_delete(y, events):
            x = nodes[y]["left"]
            t2 = nodes[x]["right"]
            events.append(f"Right rotate at {nodes[y]['value']}")
            nodes[x]["right"] = y
            nodes[y]["left"] = t2
            update_height(y)
            update_height(x)
            return x

        def rotate_left_delete(x, events):
            y = nodes[x]["right"]
            t2 = nodes[y]["left"]
            events.append(f"Left rotate at {nodes[x]['value']}")
            nodes[y]["left"] = x
            nodes[x]["right"] = t2
            update_height(x)
            update_height(y)
            return y

        def rebalance_after_delete(nid, events):
            if nid is None or nid not in nodes:
                return nid
            update_height(nid)
            bf = balance_factor(nid)
            if bf > 1:
                if balance_factor(nodes[nid]["left"]) < 0:
                    nodes[nid]["left"] = rotate_left_delete(nodes[nid]["left"], events)
                return rotate_right_delete(nid, events)
            if bf < -1:
                if balance_factor(nodes[nid]["right"]) > 0:
                    nodes[nid]["right"] = rotate_right_delete(nodes[nid]["right"], events)
                return rotate_left_delete(nid, events)
            return nid

        def delete_node(nid, val, events, path):
            if nid is None or nid not in nodes:
                events.append(f"{val} not found")
                return None

            path.append(nodes[nid]["value"])
            if val < nodes[nid]["value"]:
                nodes[nid]["left"] = delete_node(nodes[nid]["left"], val, events, path)
            elif val > nodes[nid]["value"]:
                nodes[nid]["right"] = delete_node(nodes[nid]["right"], val, events, path)
            else:
                events.append(f"Delete {val}")
                if nodes[nid]["left"] is None:
                    replacement = nodes[nid]["right"]
                    del nodes[nid]
                    return replacement
                if nodes[nid]["right"] is None:
                    replacement = nodes[nid]["left"]
                    del nodes[nid]
                    return replacement

                successor = min_node(nodes[nid]["right"])
                successor_value = nodes[successor]["value"]
                events.append(f"Replace {val} with successor {successor_value}")
                nodes[nid]["value"] = successor_value
                nodes[nid]["right"] = delete_node(nodes[nid]["right"], successor_value, events, path)

            return rebalance_after_delete(nid, events)

        def rebuild_parent_map():
            parent_map.clear()
            def walk(nid):
                if nid is None or nid not in nodes:
                    return
                for child_id in [nodes[nid]["left"], nodes[nid]["right"]]:
                    if child_id and child_id in nodes:
                        parent_map[child_id] = nid
                        walk(child_id)
            walk(root_id)

        def current_edges():
            edges = []
            for nid, nd in nodes.items():
                for child_id in [nd["left"], nd["right"]]:
                    if child_id and child_id in nodes:
                        edges.append((nid, child_id))
            return edges

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Building AVL tree from: {values_str}",
            phase="init",
        )

        for val in values:
            root_id = yield from insert(root_id, val)

        delete_values_str = str(params.get("delete_values", "")).strip()
        delete_values = []
        if delete_values_str:
            try:
                delete_values = [int(v.strip()) for v in delete_values_str.split(",") if v.strip()]
            except ValueError:
                delete_values = [v.strip() for v in delete_values_str.split(",") if v.strip()]

        for val in delete_values:
            events: list[str] = []
            path: list = []
            old_edges = current_edges()
            old_values = {nid: nd["value"] for nid, nd in nodes.items()}
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Delete {val} from AVL tree",
                phase="explore",
                state=tree_state({"delete_value": val}),
            )
            root_id = delete_node(root_id, val, events, path)
            rebuild_parent_map()
            for parent_id, child_id in old_edges:
                yield Step(
                    action=StepAction.REMOVE_EDGE,
                    target_type="edge",
                    target_id=f"{parent_id}-{child_id}",
                    value=None,
                    message="Remove stale AVL edge",
                    phase="relax",
                )
            for removed_id in sorted(set(old_values) - set(nodes)):
                yield Step(
                    action=StepAction.REMOVE_NODE,
                    target_type="node",
                    target_id=removed_id,
                    value=None,
                    message=f"Remove deleted node {removed_id}",
                    phase="relax",
                )
            for node_id, old_value in old_values.items():
                if node_id in nodes and nodes[node_id]["value"] != old_value:
                    yield Step(
                        action=StepAction.UPDATE_NODE_LABEL,
                        target_type="node",
                        target_id=node_id,
                        value=str(nodes[node_id]["value"]),
                        message=f"Update node label to successor {nodes[node_id]['value']}",
                        phase="relax",
                    )
            for parent_id, child_id in current_edges():
                yield Step(
                    action=StepAction.ADD_EDGE,
                    target_type="edge",
                    target_id=f"{parent_id}-{child_id}",
                    value={"source": parent_id, "target": child_id, "label": ""},
                    message="Add refreshed AVL edge",
                    phase="relax",
                )
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"AVL deletion of {val}: {'; '.join(events)}",
                phase="relax",
                state=tree_state({
                    "deleted_value": val,
                    "delete_path": path,
                    "rebalancing": events,
                    "delete_values": delete_values,
                }),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"AVL tree complete. {len(values)} nodes, balanced.",
            phase="result",
            state=tree_state({"deleted_values": delete_values}),
        )

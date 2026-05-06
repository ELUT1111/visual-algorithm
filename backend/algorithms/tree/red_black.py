"""Red-Black Tree - self-balancing BST with color properties."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry

RED = "red"
BLACK = "black"


@registry.register
class RedBlackAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="red_black",
            category="tree",
            description="Red-Black tree with insert, recoloring, and rotations",
            emoji="🔴",
            parameters=[
                {"name": "values", "type": "str", "required": True,
                 "description": "Comma-separated values to insert (e.g. 10,20,30,15,25)"},
            ],
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
            use_cases=[
                "Guaranteed O(log n) operations",
                "Linux kernel (CFS scheduler, memory management)",
                "Java TreeMap, C++ std::map",
                "Database indexing",
                "Balanced BST with fewer rotations than AVL",
            ],
            pseudocode=(
                "function RB_Insert(root, value):\n"
                "    node = BST_Insert(root, value)\n"
                "    node.color = RED\n"
                "    while node != root and node.parent.color == RED:\n"
                "        if uncle is RED:\n"
                "            recolor parent, uncle, grandparent\n"
                "        else:\n"
                "            rotate and recolor\n"
                "    root.color = BLACK"
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

        # Internal RB tree structure
        # id -> {"value", "left", "right", "parent", "color"}
        nodes: dict[str, dict] = {}
        node_counter = 0
        root_id = None

        def make_id():
            nonlocal node_counter
            node_counter += 1
            return f"r{node_counter}"

        def get_color(nid):
            if nid is None or nid not in nodes:
                return BLACK  # NIL nodes are black
            return nodes[nid]["color"]

        def get_parent(nid):
            if nid is None or nid not in nodes:
                return None
            return nodes[nid]["parent"]

        def get_grandparent(nid):
            p = get_parent(nid)
            if p is None:
                return None
            return get_parent(p)

        def get_sibling(nid):
            p = get_parent(nid)
            if p is None:
                return None
            if nodes[p]["left"] == nid:
                return nodes[p]["right"]
            return nodes[p]["left"]

        def get_uncle(nid):
            p = get_parent(nid)
            if p is None:
                return None
            return get_sibling(p)

        def remove_all_edges():
            """Remove all edges for re-rendering."""
            for nid, nd in nodes.items():
                for child_id in [nd["left"], nd["right"]]:
                    if child_id:
                        yield Step(
                            action=StepAction.REMOVE_EDGE,
                            target_type="edge",
                            target_id=f"{nid}-{child_id}",
                            value=None,
                            message=f"Remove edge {nid} -> {child_id}",
                            phase="relax",
                        )

        def add_all_edges():
            """Add all edges."""
            for nid, nd in nodes.items():
                for child_id in [nd["left"], nd["right"]]:
                    if child_id and child_id in nodes:
                        yield Step(
                            action=StepAction.ADD_EDGE,
                            target_type="edge",
                            target_id=f"{nid}-{child_id}",
                            value={"source": nid, "target": child_id, "label": ""},
                            message=f"Edge {nid} -> {child_id}",
                            phase="relax",
                        )

        def color_all_nodes():
            """Update colors of all nodes."""
            for nid, nd in nodes.items():
                color_val = "skipped" if nd["color"] == RED else "settled"
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=nid,
                    value=color_val,
                    message=f"Node {nd['value']}: {nd['color']}",
                    phase="relax",
                )

        def rotate_left(nid):
            nonlocal root_id
            right_id = nodes[nid]["right"]
            nodes[nid]["right"] = nodes[right_id]["left"]
            if nodes[right_id]["left"]:
                nodes[nodes[right_id]["left"]]["parent"] = nid
            nodes[right_id]["parent"] = nodes[nid]["parent"]
            if nodes[nid]["parent"] is None:
                root_id = right_id
            elif nodes[nodes[nid]["parent"]]["left"] == nid:
                nodes[nodes[nid]["parent"]]["left"] = right_id
            else:
                nodes[nodes[nid]["parent"]]["right"] = right_id
            nodes[right_id]["left"] = nid
            nodes[nid]["parent"] = right_id

        def rotate_right(nid):
            nonlocal root_id
            left_id = nodes[nid]["left"]
            nodes[nid]["left"] = nodes[left_id]["right"]
            if nodes[left_id]["right"]:
                nodes[nodes[left_id]["right"]]["parent"] = nid
            nodes[left_id]["parent"] = nodes[nid]["parent"]
            if nodes[nid]["parent"] is None:
                root_id = left_id
            elif nodes[nodes[nid]["parent"]]["left"] == nid:
                nodes[nodes[nid]["parent"]]["left"] = left_id
            else:
                nodes[nodes[nid]["parent"]]["right"] = left_id
            nodes[left_id]["right"] = nid
            nodes[nid]["parent"] = left_id

        def fix_violations(nid):
            nonlocal root_id
            while nid != root_id and get_color(nid) == RED and get_color(get_parent(nid)) == RED:
                parent = get_parent(nid)
                grandparent = get_grandparent(nid)
                uncle = get_uncle(nid)

                if get_color(uncle) == RED:
                    # Case 1: Uncle is red - recolor
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="node",
                        target_id=nid,
                        message=f"Recolor: parent {nodes[parent]['value']}, uncle {nodes[uncle]['value'] if uncle else 'NIL'} -> BLACK, grandparent {nodes[grandparent]['value']} -> RED",
                        phase="relax",
                    )
                    nodes[parent]["color"] = BLACK
                    if uncle:
                        nodes[uncle]["color"] = BLACK
                    nodes[grandparent]["color"] = RED
                    nid = grandparent
                else:
                    # Case 2/3: Uncle is black - rotate
                    if parent == nodes[grandparent]["left"]:
                        if nid == nodes[parent]["right"]:
                            # Case 2: Left-Right
                            rotate_left(parent)
                            nid = parent
                            parent = get_parent(nid)
                        # Case 3: Left-Left
                        yield Step(
                            action=StepAction.ADD_MESSAGE,
                            target_type="node",
                            target_id=nid,
                            message=f"Right rotation at {nodes[grandparent]['value']}",
                            phase="relax",
                        )
                        rotate_right(grandparent)
                        nodes[parent]["color"] = BLACK
                        nodes[grandparent]["color"] = RED
                    else:
                        if nid == nodes[parent]["left"]:
                            # Case 2: Right-Left
                            rotate_right(parent)
                            nid = parent
                            parent = get_parent(nid)
                        # Case 3: Right-Right
                        yield Step(
                            action=StepAction.ADD_MESSAGE,
                            target_type="node",
                            target_id=nid,
                            message=f"Left rotation at {nodes[grandparent]['value']}",
                            phase="relax",
                        )
                        rotate_left(grandparent)
                        nodes[parent]["color"] = BLACK
                        nodes[grandparent]["color"] = RED

                    nid = parent

            nodes[root_id]["color"] = BLACK

        def insert_value(val):
            nonlocal root_id
            new_id = make_id()
            nodes[new_id] = {"value": val, "left": None, "right": None, "parent": None, "color": RED}

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=new_id,
                value={"id": new_id, "label": str(val)},
                message=f"Insert {val} (RED)",
                phase="explore",
            )
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=new_id,
                value="skipped",
                message=f"Node {val} is RED",
                phase="explore",
            )

            if root_id is None:
                root_id = new_id
                nodes[new_id]["color"] = BLACK
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=new_id,
                    value="settled",
                    message=f"Root {val} is BLACK",
                    phase="explore",
                )
                return

            # BST insert
            current = root_id
            parent = None
            while current:
                parent = current
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=current,
                    value="current",
                    message=f"Compare {val} with {nodes[current]['value']}",
                    phase="explore",
                )
                if val < nodes[current]["value"]:
                    current = nodes[current]["left"]
                else:
                    current = nodes[current]["right"]

            nodes[new_id]["parent"] = parent
            if val < nodes[parent]["value"]:
                nodes[parent]["left"] = new_id
            else:
                nodes[parent]["right"] = new_id

            yield Step(
                action=StepAction.ADD_EDGE,
                target_type="edge",
                target_id=f"{parent}-{new_id}",
                value={"source": parent, "target": new_id, "label": ""},
                message=f"Edge {nodes[parent]['value']} -> {val}",
                phase="explore",
            )

            # Fix violations
            yield from fix_violations(new_id)

            # Re-render all edges and colors
            yield from remove_all_edges()
            yield from add_all_edges()
            yield from color_all_nodes()

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Building Red-Black tree from: {values_str}",
            phase="init",
        )

        for val in values:
            yield from insert_value(val)

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Red-Black tree complete. {len(values)} nodes, balanced.",
            phase="result",
        )

"""Segment tree range-sum visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_ints(raw: str) -> list[int]:
    return [int(item.strip()) for item in raw.split(",") if item.strip()]


def _tree_items(tree: list[int], ranges: list[tuple[int, int] | None]) -> list[dict]:
    items: list[dict] = []
    for idx in range(1, len(tree)):
        interval = ranges[idx]
        if interval is None:
            items.append({"value": "-", "meta": f"node {idx}", "state": "skipped"})
        else:
            left, right = interval
            items.append({"value": tree[idx], "meta": f"{idx}: [{left},{right}]"})
    return items


@registry.register
class SegmentTreeAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="segment_tree",
            category="tree",
            description="Build a segment tree and answer a range sum query",
            emoji="馃尶",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated integers"},
                {"name": "query_left", "type": "int", "required": False, "default": "1", "description": "0-based query left index"},
                {"name": "query_right", "type": "int", "required": False, "default": "3", "description": "0-based query right index"},
                {"name": "update_index", "type": "int", "required": False, "default": "", "description": "Optional 0-based update index"},
                {"name": "update_value", "type": "int", "required": False, "default": "", "description": "Optional updated value"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="Build O(n), query O(log n), update O(log n)",
            space_complexity="O(n)",
            use_cases=[
                "Range sum queries",
                "Point updates",
                "Interval data structures",
                "Competitive programming",
                "Query-heavy dashboards",
            ],
            pseudocode=(
                "function build(node, left, right):\n"
                "    if left == right: tree[node] = A[left]\n"
                "    else:\n"
                "        mid = (left + right) // 2\n"
                "        build(2*node, left, mid)\n"
                "        build(2*node+1, mid+1, right)\n"
                "        tree[node] = tree[2*node] + tree[2*node+1]\n"
                "\n"
                "function query(node, left, right, ql, qr):\n"
                "    if qr < left or right < ql: return 0\n"
                "    if ql <= left and right <= qr: return tree[node]\n"
                "    return query(left child) + query(right child)"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            values = _parse_ints(str(params.get("values", "")))
        except ValueError:
            return
        if not values:
            return

        n = len(values)
        tree = [0] * (4 * n)
        ranges: list[tuple[int, int] | None] = [None] * (4 * n)

        def clamp_index(raw: object, default: int) -> int:
            try:
                return int(str(raw).strip())
            except ValueError:
                return default

        ql = max(0, min(n - 1, clamp_index(params.get("query_left", 0), 0)))
        qr = max(0, min(n - 1, clamp_index(params.get("query_right", n - 1), n - 1)))
        if ql > qr:
            ql, qr = qr, ql

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="segment_tree",
            value={"title": "Segment Tree", "items": _tree_items(tree, ranges)},
            message=f"Initialize segment tree for {n} values",
            phase="init",
            state={"values": values, "query_range": [ql, qr], "tree": [], "ranges": []},
        )

        def emit_node_update(node: int, state: str, message: str, phase: str) -> Step:
            left, right = ranges[node] or (0, 0)
            return Step(
                action=StepAction.UPDATE_ARRAY_ITEM,
                target_type="array",
                target_id="segment_tree",
                value={"index": node - 1, "value": tree[node], "state": state, "meta": f"{node}: [{left},{right}]"},
                message=message,
                phase=phase,
                state={
                    "values": values,
                    "node": node,
                    "node_range": [left, right],
                    "tree": tree[1:],
                    "ranges": [list(item) if item else None for item in ranges[1:]],
                },
            )

        def build(node: int, left: int, right: int) -> Generator[Step, None, None]:
            ranges[node] = (left, right)
            yield Step(
                action=StepAction.UPDATE_ARRAY_ITEM,
                target_type="array",
                target_id="segment_tree",
                value={"index": node - 1, "value": tree[node], "state": "current", "meta": f"{node}: [{left},{right}]"},
                message=f"Create node {node} for range [{left}, {right}]",
                phase="init",
                state={"node": node, "node_range": [left, right], "values": values},
            )
            if left == right:
                tree[node] = values[left]
                yield emit_node_update(node, "sorted", f"Leaf node {node} stores value {values[left]}", "relax")
                return

            mid = (left + right) // 2
            yield from build(node * 2, left, mid)
            yield from build(node * 2 + 1, mid + 1, right)
            tree[node] = tree[node * 2] + tree[node * 2 + 1]
            yield emit_node_update(node, "updated", f"Combine children into node {node}: {tree[node]}", "relax")

        yield from build(1, 0, n - 1)

        visited: list[int] = []
        accepted: list[int] = []

        def query(node: int, left: int, right: int) -> Generator[Step, None, int]:
            visited.append(node)
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="segment_tree",
                value={"indices": [node - 1], "state": "compare"},
                message=f"Visit node {node} range [{left}, {right}] for query [{ql}, {qr}]",
                phase="explore",
                state={"query_range": [ql, qr], "visited_nodes": list(visited), "accepted_nodes": list(accepted)},
            )

            if right < ql or qr < left:
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="segment_tree",
                    value={"indices": [node - 1], "state": "skipped"},
                    message=f"Range [{left}, {right}] is outside the query",
                    phase="explore",
                    state={"query_range": [ql, qr], "visited_nodes": list(visited), "accepted_nodes": list(accepted)},
                )
                return 0

            if ql <= left and right <= qr:
                accepted.append(node)
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="segment_tree",
                    value={"indices": [node - 1], "state": "sorted"},
                    message=f"Use node {node} value {tree[node]} for covered range [{left}, {right}]",
                    phase="relax",
                    state={
                        "query_range": [ql, qr],
                        "accepted_nodes": list(accepted),
                        "partial_sum": sum(tree[item] for item in accepted),
                    },
                )
                return tree[node]

            mid = (left + right) // 2
            left_sum = yield from query(node * 2, left, mid)
            right_sum = yield from query(node * 2 + 1, mid + 1, right)
            subtotal = left_sum + right_sum
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="array",
                target_id="segment_tree",
                message=f"Node {node} contributes {subtotal} from its children",
                phase="relax",
                state={"query_range": [ql, qr], "node": node, "subtotal": subtotal},
            )
            return subtotal

        query_sum = yield from query(1, 0, n - 1)

        update_raw = str(params.get("update_index", "")).strip()
        value_raw = str(params.get("update_value", "")).strip()
        update_applied = False

        def update(node: int, left: int, right: int, index: int, new_value: int) -> Generator[Step, None, None]:
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="segment_tree",
                value={"indices": [node - 1], "state": "current"},
                message=f"Update visits node {node} range [{left}, {right}]",
                phase="explore",
                state={"update_index": index, "update_value": new_value, "node": node, "node_range": [left, right]},
            )
            if left == right:
                values[index] = new_value
                tree[node] = new_value
                yield emit_node_update(node, "updated", f"Set leaf {node} to {new_value}", "relax")
                return

            mid = (left + right) // 2
            if index <= mid:
                yield from update(node * 2, left, mid, index, new_value)
            else:
                yield from update(node * 2 + 1, mid + 1, right, index, new_value)
            tree[node] = tree[node * 2] + tree[node * 2 + 1]
            yield emit_node_update(node, "updated", f"Refresh node {node} to {tree[node]}", "relax")

        if update_raw != "" and value_raw != "":
            try:
                update_index = int(update_raw)
                update_value = int(value_raw)
            except ValueError:
                update_index = -1
                update_value = 0
            if 0 <= update_index < n:
                update_applied = True
                yield from update(1, 0, n - 1, update_index, update_value)

        final_state = {
            "values": values,
            "tree": tree[1:],
            "ranges": [list(item) if item else None for item in ranges[1:]],
            "query_range": [ql, qr],
            "accepted_nodes": accepted,
            "range_sum": query_sum,
            "update_applied": update_applied,
        }

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="segment_tree",
            message=f"Range sum [{ql}, {qr}] = {query_sum}",
            phase="result",
            state=final_state,
        )

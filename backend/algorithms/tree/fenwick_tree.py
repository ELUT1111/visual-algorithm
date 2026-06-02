"""Fenwick tree prefix-sum visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _items(values: list[int], tree: list[int]) -> list[dict]:
    return [
        {"value": idx, "meta": f"v={values[idx - 1]} bit={tree[idx]}"}
        for idx in range(1, len(tree))
    ]


@registry.register
class FenwickTreeAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="fenwick_tree",
            category="tree",
            description="Build a Fenwick tree and answer a prefix sum query",
            emoji="🌿",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated integers"},
                {"name": "query_index", "type": "int", "required": False, "default": "", "description": "1-based prefix end index"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="Build O(n log n), query O(log n)",
            space_complexity="O(n)",
            use_cases=[
                "Prefix sum queries",
                "Range-sum data structures",
                "Competitive programming",
                "Incremental updates",
            ],
            pseudocode=(
                "function add(i, value):\n"
                "    while i <= n:\n"
                "        bit[i] += value\n"
                "        i += i & -i\n"
                "\n"
                "function prefix_sum(i):\n"
                "    sum = 0\n"
                "    while i > 0:\n"
                "        sum += bit[i]\n"
                "        i -= i & -i"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        raw = str(params.get("values", ""))
        try:
            values = [int(item.strip()) for item in raw.split(",") if item.strip()]
        except ValueError:
            return
        if not values:
            return

        n = len(values)
        tree = [0] * (n + 1)
        query_raw = str(params.get("query_index", "")).strip()
        query_index = int(query_raw) if query_raw.isdigit() else n
        query_index = max(1, min(n, query_index))

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="fenwick",
            value={"title": "Fenwick Tree", "items": _items(values, tree)},
            message="Initialize Fenwick tree array",
            phase="init",
            state={"values": values, "tree": tree[1:], "query_index": query_index},
        )

        for source_idx, value in enumerate(values, start=1):
            idx = source_idx
            while idx <= n:
                tree[idx] += value
                yield Step(
                    action=StepAction.UPDATE_ARRAY_ITEM,
                    target_type="array",
                    target_id="fenwick",
                    value={"index": idx - 1, "value": idx, "state": "updated", "meta": f"bit={tree[idx]}"},
                    message=f"Add value {value} from index {source_idx} to BIT[{idx}]",
                    phase="relax",
                    state={
                        "source_index": source_idx,
                        "update_index": idx,
                        "lowbit": idx & -idx,
                        "tree": tree[1:],
                    },
                )
                idx += idx & -idx

        total = 0
        cursor = query_index
        path: list[int] = []
        while cursor > 0:
            path.append(cursor)
            total += tree[cursor]
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="fenwick",
                value={"indices": [cursor - 1], "state": "compare"},
                message=f"Query visits BIT[{cursor}], running sum {total}",
                phase="explore",
                state={
                    "query_index": query_index,
                    "query_path": list(path),
                    "running_sum": total,
                    "tree": tree[1:],
                },
            )
            cursor -= cursor & -cursor

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="fenwick",
            message=f"Prefix sum 1..{query_index} = {total}",
            phase="result",
            state={
                "values": values,
                "tree": tree[1:],
                "query_index": query_index,
                "query_path": path,
                "prefix_sum": total,
            },
        )

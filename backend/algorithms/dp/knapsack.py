"""0/1 knapsack dynamic programming visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_ints(values_str: str) -> list[int]:
    return [int(v.strip()) for v in values_str.split(",") if v.strip()]


@registry.register
class KnapsackAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="knapsack",
            category="dp",
            description="Solve the 0/1 knapsack problem with a capacity table",
            emoji="🎒",
            parameters=[
                {"name": "weights", "type": "str", "required": True, "description": "Comma-separated item weights"},
                {"name": "capacity", "type": "int", "required": True, "description": "Maximum capacity"},
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated item values"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="matrix",
            time_complexity="O(nW)",
            space_complexity="O(nW)",
            use_cases=[
                "Resource allocation",
                "Budgeted selection",
                "Packing optimization",
                "Dynamic programming teaching",
            ],
            pseudocode=(
                "function Knapsack(weights, values, capacity):\n"
                "    dp = zero matrix of (items + 1) x (capacity + 1)\n"
                "    for item from 1 to n:\n"
                "        for cap from 0 to capacity:\n"
                "            dp[item][cap] = dp[item-1][cap]\n"
                "            if weight[item] <= cap:\n"
                "                dp[item][cap] = max(dp[item][cap], value[item] + dp[item-1][cap-weight[item]])\n"
                "    return dp[n][capacity]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            weights = _parse_ints(str(params.get("weights", "")))
            values = _parse_ints(str(params.get("values", "")))
            capacity = int(params.get("capacity", 0))
        except ValueError:
            return

        n = min(len(weights), len(values))
        weights = weights[:n]
        values = values[:n]
        if n == 0 or capacity < 0:
            return

        rows = ["0"] + [f"{idx}:w{weights[idx - 1]}/v{values[idx - 1]}" for idx in range(1, n + 1)]
        cols = [str(cap) for cap in range(capacity + 1)]
        dp = [[0 for _ in cols] for _ in rows]

        def matrix_payload() -> dict:
            return {
                "title": "0/1 Knapsack",
                "rows": rows,
                "columns": cols,
                "values": [[value for value in row] for row in dp],
            }

        yield Step(
            action=StepAction.RENDER_MATRIX,
            target_type="matrix",
            target_id="knapsack",
            value=matrix_payload(),
            message=f"Build knapsack table for {n} item(s), capacity {capacity}",
            phase="init",
            state={"weights": weights, "values": values, "capacity": capacity},
        )

        for item in range(1, n + 1):
            weight = weights[item - 1]
            value = values[item - 1]
            for cap in range(capacity + 1):
                yield Step(
                    action=StepAction.HIGHLIGHT_MATRIX_CELL,
                    target_type="matrix",
                    target_id="knapsack",
                    value={"row": item, "col": cap, "state": "current"},
                    message=f"Consider item {item} (w={weight}, v={value}) at capacity {cap}",
                    phase="explore",
                    state={"item": item, "weight": weight, "value": value, "capacity": cap},
                )

                without_item = dp[item - 1][cap]
                with_item = None
                best = without_item
                if weight <= cap:
                    with_item = value + dp[item - 1][cap - weight]
                    best = max(without_item, with_item)
                dp[item][cap] = best

                if with_item is None:
                    message = f"Item is too heavy; keep previous best {without_item}"
                else:
                    message = f"max(skip {without_item}, take {with_item}) = {best}"

                yield Step(
                    action=StepAction.UPDATE_MATRIX_CELL,
                    target_type="matrix",
                    target_id="knapsack",
                    value={"row": item, "col": cap, "value": best, "state": "updated"},
                    message=message,
                    phase="relax",
                    state={
                        "item": item,
                        "capacity": cap,
                        "skip": without_item,
                        "take": with_item,
                        "best": best,
                    },
                )

        selected: list[int] = []
        backtrack_path: list[dict] = []
        cap = capacity
        for item in range(n, 0, -1):
            if dp[item][cap] != dp[item - 1][cap]:
                backtrack_path.append(
                    {
                        "row": item,
                        "capacity": cap,
                        "item_index": item - 1,
                        "weight": weights[item - 1],
                        "value": values[item - 1],
                        "decision": "take",
                        "next_capacity": cap - weights[item - 1],
                    }
                )
                selected.append(item - 1)
                cap -= weights[item - 1]
            else:
                backtrack_path.append(
                    {
                        "row": item,
                        "capacity": cap,
                        "item_index": item - 1,
                        "weight": weights[item - 1],
                        "value": values[item - 1],
                        "decision": "skip",
                        "next_capacity": cap,
                    }
                )
        selected.reverse()
        backtrack_path.reverse()
        path_cells = [{"row": step["row"], "col": step["capacity"], "state": "path"} for step in backtrack_path]
        selected_items = [
            {"index": idx, "weight": weights[idx], "value": values[idx]}
            for idx in selected
        ]

        yield Step(
            action=StepAction.HIGHLIGHT_MATRIX_CELL,
            target_type="matrix",
            target_id="knapsack",
            value={"cells": path_cells or [{"row": n, "col": capacity, "state": "path"}], "state": "path"},
            message=f"Best value is {dp[n][capacity]} with item indices {selected}",
            phase="result",
            state={
                "max_value": dp[n][capacity],
                "selected_indices": selected,
                "selected_items": selected_items,
                "backtrack_path": backtrack_path,
                "path_cells": path_cells,
                "total_weight": sum(weights[idx] for idx in selected),
            },
        )

"""Subset sum dynamic programming visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_values(values_str: str) -> list[int]:
    return [int(v.strip()) for v in values_str.split(",") if v.strip()]


@registry.register
class SubsetSumAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="subset_sum",
            category="dp",
            description="Determine whether a subset reaches the target sum",
            emoji="🧩",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated non-negative numbers"},
                {"name": "target", "type": "int", "required": True, "description": "Target sum"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="matrix",
            time_complexity="O(nT)",
            space_complexity="O(nT)",
            use_cases=[
                "Budget partitioning",
                "Feasibility checks",
                "Backtracking education",
                "Knapsack-style reasoning",
            ],
            pseudocode=(
                "function SubsetSum(A, target):\n"
                "    dp[0][0] = true\n"
                "    for i from 1 to n:\n"
                "        for s from 0 to target:\n"
                "            dp[i][s] = dp[i-1][s] or dp[i-1][s-A[i-1]]\n"
                "    return dp[n][target]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            values = _parse_values(str(params.get("values", "")))
            target = int(params.get("target", 0))
        except ValueError:
            return
        if not values or target < 0 or any(v < 0 for v in values):
            return

        n = len(values)
        rows = ["0"] + [f"{idx + 1}:{value}" for idx, value in enumerate(values)]
        cols = [str(s) for s in range(target + 1)]
        dp = [[False for _ in cols] for _ in rows]
        dp[0][0] = True

        def matrix_state() -> dict:
            return {
                "title": "Subset Sum",
                "rows": rows,
                "columns": cols,
                "values": [["T" if cell else "F" for cell in row] for row in dp],
            }

        yield Step(
            action=StepAction.RENDER_MATRIX,
            target_type="matrix",
            target_id="subset_sum",
            value=matrix_state(),
            message=f"Build subset-sum table for values {values} and target {target}",
            phase="init",
            state={"values": values, "target": target, "subset_found": False, "dp_table": matrix_state()},
        )

        for i in range(1, n + 1):
            value = values[i - 1]
            dp[i][0] = True
            for s in range(1, target + 1):
                take = s >= value and dp[i - 1][s - value]
                skip = dp[i - 1][s]
                dp[i][s] = skip or take

                yield Step(
                    action=StepAction.HIGHLIGHT_MATRIX_CELL,
                    target_type="matrix",
                    target_id="subset_sum",
                    value={"row": i, "col": s, "state": "current"},
                    message=f"Check value {value} for sum {s}",
                    phase="explore",
                    state={"item": i, "sum": s, "take": take, "skip": skip, "dp_table": matrix_state()},
                )

                yield Step(
                    action=StepAction.UPDATE_MATRIX_CELL,
                    target_type="matrix",
                    target_id="subset_sum",
                    value={"row": i, "col": s, "value": "T" if dp[i][s] else "F", "state": "updated"},
                    message=f"dp[{i}][{s}] = {'T' if dp[i][s] else 'F'}",
                    phase="relax",
                    state={"item": i, "sum": s, "reachable": dp[i][s], "dp_table": matrix_state()},
                )

        selected: list[int] = []
        backtrack_path: list[dict] = []
        if dp[n][target]:
            s = target
            for i in range(n, 0, -1):
                if s >= values[i - 1] and dp[i - 1][s - values[i - 1]]:
                    backtrack_path.append(
                        {
                            "row": i,
                            "sum": s,
                            "value": values[i - 1],
                            "item_index": i - 1,
                            "decision": "take",
                            "next_sum": s - values[i - 1],
                        }
                    )
                    selected.append(i - 1)
                    s -= values[i - 1]
                else:
                    backtrack_path.append(
                        {
                            "row": i,
                            "sum": s,
                            "value": values[i - 1],
                            "item_index": i - 1,
                            "decision": "skip",
                            "next_sum": s,
                        }
                    )
            selected.reverse()
            backtrack_path.reverse()

        path_cells = [{"row": step["row"], "col": step["sum"], "state": "path"} for step in backtrack_path]
        selected_values = [values[idx] for idx in selected]

        yield Step(
            action=StepAction.HIGHLIGHT_MATRIX_CELL,
            target_type="matrix",
            target_id="subset_sum",
            value={
                "cells": path_cells or [{"row": n, "col": target, "state": "skipped"}],
                "state": "path" if dp[n][target] else "skipped",
            },
            message=(
                f"Subset sum {'found' if dp[n][target] else 'not found'} for target {target}"
            ),
            phase="result",
            state={
                "subset_found": dp[n][target],
                "selected_indices": selected,
                "selected_values": selected_values,
                "selected_sum": sum(selected_values),
                "backtrack_path": backtrack_path,
                "path_cells": path_cells,
                "target": target,
                "values": values,
                "dp_table": matrix_state(),
            },
        )

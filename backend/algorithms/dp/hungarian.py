"""Hungarian-style assignment solver visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_matrix(raw: str) -> list[list[int]]:
    rows: list[list[int]] = []
    for row in raw.split(";"):
        values = [int(item.strip()) for item in row.split(",") if item.strip()]
        if values:
            rows.append(values)
    if not rows:
        return []
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return []
    return rows


@registry.register
class HungarianAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="hungarian",
            category="dp",
            description="Minimum-cost assignment with row/column reduction and exact DP search",
            emoji="HA",
            parameters=[
                {"name": "costs", "type": "str", "required": True, "description": "Rows separated by ; and columns by ,"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="matrix",
            time_complexity="O(n^3) for the Hungarian method; O(n 2^n) shown for exact assignment DP",
            space_complexity="O(n 2^n)",
            use_cases=[
                "Worker-task assignment",
                "Minimum-cost matching",
                "Scheduling optimization",
                "Operations research education",
            ],
            pseudocode=(
                "reduce every row by its minimum\n"
                "reduce every column by its minimum\n"
                "solve assignment on the reduced matrix\n"
                "choose one unique column per row with minimum total cost"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        costs = _parse_matrix(str(params.get("costs", "")))
        if not costs:
            return

        n = len(costs)
        m = len(costs[0])
        if n > m:
            return

        reduced = [row[:] for row in costs]
        rows = [f"W{i}" for i in range(n)]
        cols = [f"T{j}" for j in range(m)]

        def payload(title: str, matrix: list[list[int]], highlights: list[dict] | None = None) -> dict:
            return {"title": title, "rows": rows, "columns": cols, "values": matrix, "highlights": highlights or []}

        yield Step(
            action=StepAction.RENDER_MATRIX,
            target_type="matrix",
            target_id="hungarian",
            value=payload("Hungarian Cost Matrix", reduced),
            message="Load assignment cost matrix",
            phase="init",
            state={"cost_matrix": costs, "reduced_matrix": reduced},
        )

        row_reductions: list[int] = []
        for i, row in enumerate(reduced):
            row_min = min(row)
            row_reductions.append(row_min)
            reduced[i] = [value - row_min for value in row]
            yield Step(
                action=StepAction.RENDER_MATRIX,
                target_type="matrix",
                target_id="hungarian",
                value=payload("Row Reduction", reduced, [{"row": i, "col": j, "state": "updated"} for j in range(m)]),
                message=f"Subtract row {i} minimum {row_min}",
                phase="relax",
                state={"row_reductions": list(row_reductions), "reduced_matrix": [row[:] for row in reduced]},
            )

        col_reductions: list[int] = []
        for j in range(m):
            col_min = min(reduced[i][j] for i in range(n))
            col_reductions.append(col_min)
            for i in range(n):
                reduced[i][j] -= col_min
            yield Step(
                action=StepAction.RENDER_MATRIX,
                target_type="matrix",
                target_id="hungarian",
                value=payload("Column Reduction", reduced, [{"row": i, "col": j, "state": "updated"} for i in range(n)]),
                message=f"Subtract column {j} minimum {col_min}",
                phase="relax",
                state={"column_reductions": list(col_reductions), "reduced_matrix": [row[:] for row in reduced]},
            )

        total_masks = 1 << m
        inf = 10**12
        dp = [[inf] * total_masks for _ in range(n + 1)]
        parent: list[list[tuple[int, int] | None]] = [[None] * total_masks for _ in range(n + 1)]
        dp[0][0] = 0

        for i in range(n):
            for mask in range(total_masks):
                if dp[i][mask] >= inf:
                    continue
                for j in range(m):
                    if mask & (1 << j):
                        continue
                    next_mask = mask | (1 << j)
                    candidate = dp[i][mask] + costs[i][j]
                    yield Step(
                        action=StepAction.HIGHLIGHT_MATRIX_CELL,
                        target_type="matrix",
                        target_id="hungarian",
                        value={"row": i, "col": j, "state": "compare"},
                        message=f"Try assign worker {i} to task {j}: cost {candidate}",
                        phase="explore",
                        state={"worker": i, "task": j, "mask": mask, "candidate_cost": candidate},
                    )
                    if candidate < dp[i + 1][next_mask]:
                        dp[i + 1][next_mask] = candidate
                        parent[i + 1][next_mask] = (mask, j)

        best_mask = min(range(total_masks), key=lambda mask: dp[n][mask])
        min_cost = dp[n][best_mask]
        assignment: list[dict] = []
        mask = best_mask
        for i in range(n, 0, -1):
            prev = parent[i][mask]
            if prev is None:
                break
            prev_mask, task = prev
            assignment.append({"worker": i - 1, "task": task, "cost": costs[i - 1][task]})
            mask = prev_mask
        assignment.reverse()

        highlights = [{"row": item["worker"], "col": item["task"], "state": "path"} for item in assignment]
        yield Step(
            action=StepAction.RENDER_MATRIX,
            target_type="matrix",
            target_id="hungarian",
            value=payload("Optimal Assignment", costs, highlights),
            message=f"Hungarian assignment complete. Minimum cost = {min_cost}",
            phase="result",
            state={
                "cost_matrix": costs,
                "reduced_matrix": reduced,
                "assignment": assignment,
                "min_cost": min_cost,
                "row_reductions": row_reductions,
                "column_reductions": col_reductions,
            },
        )

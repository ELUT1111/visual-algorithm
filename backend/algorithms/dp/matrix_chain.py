"""Matrix chain multiplication dynamic programming visualization."""
from __future__ import annotations

from math import inf
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_dimensions(dimensions_str: str) -> list[int]:
    return [int(v.strip()) for v in dimensions_str.split(",") if v.strip()]


def _build_parenthesization(split: list[list[int | None]], i: int, j: int) -> str:
    if i == j:
        return f"A{i + 1}"
    k = split[i][j]
    if k is None:
        return f"A{i + 1}..A{j + 1}"
    return f"({_build_parenthesization(split, i, k)}{_build_parenthesization(split, k + 1, j)})"


def _build_parenthesization_tree(split: list[list[int | None]], i: int, j: int) -> dict:
    if i == j:
        return {"name": f"A{i + 1}", "start": i, "end": j}
    k = split[i][j]
    if k is None:
        return {"name": f"A{i + 1}..A{j + 1}", "start": i, "end": j}
    return {
        "name": f"A{i + 1}..A{j + 1}",
        "start": i,
        "end": j,
        "split": k,
        "left": _build_parenthesization_tree(split, i, k),
        "right": _build_parenthesization_tree(split, k + 1, j),
    }


def _build_split_trace(split: list[list[int | None]], i: int, j: int) -> list[dict]:
    if i == j:
        return [{"start": i, "end": j, "matrix": f"A{i + 1}", "decision": "leaf"}]
    k = split[i][j]
    if k is None:
        return [{"start": i, "end": j, "decision": "unknown"}]
    return [
        {"start": i, "end": j, "split": k, "decision": f"split after A{k + 1}"},
        *_build_split_trace(split, i, k),
        *_build_split_trace(split, k + 1, j),
    ]


@registry.register
class MatrixChainAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="matrix_chain_multiplication",
            category="dp",
            description="Minimize scalar multiplications for matrix chain multiplication",
            emoji="🔗",
            parameters=[
                {"name": "dimensions", "type": "str", "required": True, "description": "Comma-separated dimensions"}
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="matrix",
            time_complexity="O(n^3)",
            space_complexity="O(n^2)",
            use_cases=[
                "Compiler optimization",
                "Expression evaluation planning",
                "Dynamic programming education",
                "Linear algebra planning",
            ],
            pseudocode=(
                "function MatrixChain(p):\n"
                "    for i in range(n): dp[i][i] = 0\n"
                "    for length from 2 to n:\n"
                "        for i from 0 to n-length:\n"
                "            j = i + length - 1\n"
                "            dp[i][j] = min over k of dp[i][k] + dp[k+1][j] + p[i]*p[k+1]*p[j+1]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            dimensions = _parse_dimensions(str(params.get("dimensions", "")))
        except ValueError:
            return
        if len(dimensions) < 3:
            return

        n = len(dimensions) - 1
        dp = [[0 if i == j else inf for j in range(n)] for i in range(n)]
        split: list[list[int | None]] = [[None for _ in range(n)] for _ in range(n)]
        names = [f"A{i + 1}" for i in range(n)]

        def matrix_state() -> dict:
            return {
                "title": "Matrix Chain Cost",
                "rows": names,
                "columns": names,
                "values": [[("∞" if value == inf else int(value)) for value in row] for row in dp],
            }

        yield Step(
            action=StepAction.RENDER_MATRIX,
            target_type="matrix",
            target_id="matrix_chain",
            value=matrix_state(),
            message=f"Build matrix-chain table for dimensions {dimensions}",
            phase="init",
            state={"dimensions": dimensions, "cost_table": matrix_state(), "split_table": split},
        )

        for length in range(2, n + 1):
            for i in range(0, n - length + 1):
                j = i + length - 1
                best = inf
                best_k: int | None = None

                yield Step(
                    action=StepAction.HIGHLIGHT_MATRIX_CELL,
                    target_type="matrix",
                    target_id="matrix_chain",
                    value={"row": i, "col": j, "state": "current"},
                    message=f"Solve chain {names[i]}..{names[j]}",
                    phase="explore",
                    state={"i": i, "j": j, "length": length, "cost_table": matrix_state(), "split_table": split},
                )

                for k in range(i, j):
                    cost = dp[i][k] + dp[k + 1][j] + dimensions[i] * dimensions[k + 1] * dimensions[j + 1]
                    if cost < best:
                        best = cost
                        best_k = k

                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="matrix",
                        target_id="matrix_chain",
                        message=f"Try split at {k + 1}: cost = {cost}",
                        phase="relax",
                        state={
                            "i": i,
                            "j": j,
                            "k": k,
                            "candidate_cost": cost,
                            "best_cost": best,
                            "best_split": best_k,
                        },
                    )

                dp[i][j] = best
                split[i][j] = best_k
                yield Step(
                    action=StepAction.UPDATE_MATRIX_CELL,
                    target_type="matrix",
                    target_id="matrix_chain",
                    value={"row": i, "col": j, "value": int(best), "state": "updated"},
                    message=f"dp[{i}][{j}] = {int(best)}",
                    phase="relax",
                    state={"i": i, "j": j, "best_cost": int(best), "best_split": best_k, "split_table": split},
                )

        parenthesization = _build_parenthesization(split, 0, n - 1)
        parenthesization_tree = _build_parenthesization_tree(split, 0, n - 1)
        split_trace = _build_split_trace(split, 0, n - 1)
        yield Step(
            action=StepAction.HIGHLIGHT_MATRIX_CELL,
            target_type="matrix",
            target_id="matrix_chain",
            value={"row": 0, "col": n - 1, "state": "path"},
            message=f"Optimal parenthesization: {parenthesization}",
            phase="result",
            state={
                "min_cost": int(dp[0][n - 1]),
                "parenthesization": parenthesization,
                "parenthesization_tree": parenthesization_tree,
                "split_trace": split_trace,
                "dimensions": dimensions,
                "cost_table": matrix_state(),
                "split_table": split,
            },
        )

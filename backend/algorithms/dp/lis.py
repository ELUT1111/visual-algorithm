"""Longest increasing subsequence visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_values(values_str: str) -> list[int]:
    return [int(v.strip()) for v in values_str.split(",") if v.strip()]


@registry.register
class LISAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="lis",
            category="dp",
            description="Find the longest increasing subsequence with DP lengths per item",
            emoji="📈",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated numbers"}
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n^2)",
            space_complexity="O(n)",
            use_cases=[
                "Sequence analysis",
                "Trend detection",
                "Dynamic programming teaching",
                "Ordering constraints",
            ],
            pseudocode=(
                "function LIS(A):\n"
                "    dp[i] = 1 for every i\n"
                "    prev[i] = -1 for every i\n"
                "    for i from 0 to n - 1:\n"
                "        for j from 0 to i - 1:\n"
                "            if A[j] < A[i] and dp[j] + 1 > dp[i]:\n"
                "                dp[i] = dp[j] + 1\n"
                "                prev[i] = j\n"
                "    reconstruct sequence from the best index"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            values = _parse_values(str(params.get("values", "")))
        except ValueError:
            return
        if not values:
            return

        dp = [1 for _ in values]
        prev = [-1 for _ in values]

        def items() -> list[dict]:
            return [{"value": value, "meta": f"len={dp[idx]}"} for idx, value in enumerate(values)]

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Longest Increasing Subsequence", "items": items()},
            message=f"Initial sequence: {values}",
            phase="init",
            state={"array": values, "lengths": list(dp), "previous": list(prev)},
        )

        for i in range(len(values)):
            for j in range(i):
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": [j, i], "state": "compare"},
                    message=f"Can {values[j]} extend to {values[i]}?",
                    phase="explore",
                    state={"i": i, "j": j, "lengths": list(dp), "previous": list(prev)},
                )

                if values[j] < values[i] and dp[j] + 1 > dp[i]:
                    dp[i] = dp[j] + 1
                    prev[i] = j
                    yield Step(
                        action=StepAction.UPDATE_ARRAY_ITEM,
                        target_type="array",
                        target_id="main",
                        value={"index": i, "value": values[i], "state": "swapped", "meta": f"len={dp[i]}"},
                        message=f"Update LIS length at index {i} to {dp[i]} via index {j}",
                        phase="relax",
                        state={"i": i, "j": j, "lengths": list(dp), "previous": list(prev)},
                    )

        best_index = max(range(len(values)), key=lambda idx: dp[idx])
        sequence_indices: list[int] = []
        cursor = best_index
        while cursor != -1:
            sequence_indices.append(cursor)
            cursor = prev[cursor]
        sequence_indices.reverse()
        sequence = [values[idx] for idx in sequence_indices]

        yield Step(
            action=StepAction.HIGHLIGHT_ARRAY_ITEM,
            target_type="array",
            target_id="main",
            value={"indices": sequence_indices, "state": "sorted"},
            message=f"LIS result: {sequence} (length {dp[best_index]})",
            phase="result",
            state={"length": dp[best_index], "sequence": sequence, "indices": sequence_indices},
        )

"""Kadane's maximum subarray algorithm visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_values(values_str: str) -> list[int]:
    return [int(v.strip()) for v in values_str.split(",") if v.strip()]


def _decision_row(
    index: int,
    value: int,
    current_sum: int,
    best_sum: int,
    current_start: int,
    best_start: int,
    best_end: int,
    decision: str,
) -> dict:
    return {
        "index": index,
        "value": value,
        "current_sum": current_sum,
        "best_sum": best_sum,
        "current_window": {"start": current_start, "end": index},
        "best_window": {"start": best_start, "end": best_end},
        "decision": decision,
    }


@registry.register
class KadaneAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="kadane",
            category="array",
            description="Find the maximum-sum contiguous subarray in one pass",
            emoji="📈",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated numbers"}
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n)",
            space_complexity="O(1)",
            use_cases=[
                "Maximum profit/loss window",
                "Signal and time-series analysis",
                "Dynamic programming on arrays",
                "Contiguous segment optimization",
            ],
            pseudocode=(
                "function Kadane(A):\n"
                "    best = current = A[0]\n"
                "    for i from 1 to len(A)-1:\n"
                "        current = max(A[i], current + A[i])\n"
                "        best = max(best, current)\n"
                "    return best"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            values = _parse_values(str(params.get("values", "")))
        except ValueError:
            return
        if not values:
            return

        items = [{"value": value, "meta": ""} for value in values]
        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Kadane Maximum Subarray", "items": items},
            message=f"Initial array: {values}",
            phase="init",
            state={"array": values},
        )

        current_sum = values[0]
        best_sum = values[0]
        current_start = 0
        best_start = 0
        best_end = 0
        trace: list[dict] = []

        yield Step(
            action=StepAction.UPDATE_ARRAY_ITEM,
            target_type="array",
            target_id="main",
            value={"index": 0, "value": values[0], "state": "current", "meta": f"cur={current_sum} best={best_sum}"},
            message=f"Start at index 0 with sum {current_sum}",
            phase="init",
            state={
                "index": 0,
                "current_sum": current_sum,
                "best_sum": best_sum,
                "current_range": [current_start, 0],
                "best_range": [best_start, best_end],
                "decision": "seed",
                "trace": list(trace),
            },
        )

        for idx in range(1, len(values)):
            value = values[idx]
            extend_sum = current_sum + value
            start_new = value
            decision = "start new subarray" if start_new > extend_sum else "extend current subarray"

            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": [idx], "state": "compare"},
                message=f"Compare starting new at {value} vs extending to {extend_sum}",
                phase="explore",
                state={
                    "index": idx,
                    "value": value,
                    "decision_candidates": {
                        "start_new": start_new,
                        "extend": extend_sum,
                    },
                    "current_sum": current_sum,
                    "best_sum": best_sum,
                    "current_window": {"start": current_start, "end": idx - 1},
                    "best_window": {"start": best_start, "end": best_end},
                    "trace": list(trace),
                },
            )

            if start_new > extend_sum:
                current_sum = value
                current_start = idx
            else:
                current_sum = extend_sum

            if current_sum > best_sum:
                best_sum = current_sum
                best_start = current_start
                best_end = idx
                best_message = f"; new best range [{best_start}, {best_end}]"
            else:
                best_message = ""

            trace.append(
                _decision_row(
                    idx,
                    value,
                    current_sum,
                    best_sum,
                    current_start,
                    best_start,
                    best_end,
                    decision,
                )
            )

            yield Step(
                action=StepAction.UPDATE_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"index": idx, "value": value, "state": "current", "meta": f"cur={current_sum} best={best_sum}"},
                message=f"{decision}: current sum {current_sum}{best_message}",
                phase="relax",
                state={
                    "index": idx,
                    "current_sum": current_sum,
                    "best_sum": best_sum,
                    "current_range": [current_start, idx],
                    "best_range": [best_start, best_end],
                    "decision": decision,
                    "trace": list(trace),
                },
            )

        best_indices = list(range(best_start, best_end + 1))
        yield Step(
            action=StepAction.HIGHLIGHT_ARRAY_ITEM,
            target_type="array",
            target_id="main",
            value={"indices": best_indices, "state": "sorted"},
            message=f"Maximum subarray sum is {best_sum}: {values[best_start:best_end + 1]}",
            phase="result",
            state={
                "max_sum": best_sum,
                "start": best_start,
                "end": best_end,
                "subarray": values[best_start:best_end + 1],
                "trace": list(trace),
                "best_window": {"start": best_start, "end": best_end},
            },
        )

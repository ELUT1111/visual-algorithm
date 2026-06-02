"""Merge sort with array visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_values(values_str: str) -> list[int | str]:
    try:
        return [int(v.strip()) for v in values_str.split(",") if v.strip()]
    except ValueError:
        return [v.strip() for v in values_str.split(",") if v.strip()]


@registry.register
class MergeSortAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="merge_sort",
            category="array",
            description="Sort values by recursively merging sorted halves",
            emoji="🔀",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated values"}
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            use_cases=["Stable sorting", "External sorting", "Divide and conquer teaching"],
            pseudocode=(
                "function MergeSort(A):\n"
                "    split A into left and right halves\n"
                "    MergeSort(left); MergeSort(right)\n"
                "    merge the two sorted halves"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        values = _parse_values(params.get("values", ""))
        if not values:
            return

        def state(lo: int | None = None, hi: int | None = None) -> dict:
            result = {"array": list(values)}
            if lo is not None and hi is not None:
                result["range"] = [lo, hi]
            return result

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Merge Sort", "items": [{"value": value} for value in values]},
            message=f"Initial array: {values}",
            phase="init",
            state=state(),
        )

        def merge(lo: int, mid: int, hi: int) -> Generator[Step, None, None]:
            left = values[lo : mid + 1]
            right = values[mid + 1 : hi + 1]
            i = j = 0
            k = lo

            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": list(range(lo, hi + 1)), "state": "compare"},
                message=f"Merge ranges [{lo}, {mid}] and [{mid + 1}, {hi}]",
                phase="explore",
                state={**state(lo, hi), "left": list(left), "right": list(right)},
            )

            while i < len(left) and j < len(right):
                if left[i] <= right[j]:
                    values[k] = left[i]
                    i += 1
                else:
                    values[k] = right[j]
                    j += 1

                yield Step(
                    action=StepAction.UPDATE_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"index": k, "value": values[k], "state": "swapped", "meta": "merge"},
                    message=f"Write {values[k]} at index {k}",
                    phase="relax",
                    state={**state(lo, hi), "left_remaining": left[i:], "right_remaining": right[j:]},
                )
                k += 1

            for remaining in (left[i:], right[j:]):
                for item in remaining:
                    values[k] = item
                    yield Step(
                        action=StepAction.UPDATE_ARRAY_ITEM,
                        target_type="array",
                        target_id="main",
                        value={"index": k, "value": item, "state": "swapped", "meta": "merge"},
                        message=f"Copy remaining {item} to index {k}",
                        phase="relax",
                        state=state(lo, hi),
                    )
                    k += 1

        def mergesort(lo: int, hi: int) -> Generator[Step, None, None]:
            if lo >= hi:
                return
            mid = (lo + hi) // 2
            yield from mergesort(lo, mid)
            yield from mergesort(mid + 1, hi)
            yield from merge(lo, mid, hi)

        yield from mergesort(0, len(values) - 1)

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Merge Sort", "items": [{"value": value, "state": "sorted"} for value in values]},
            message=f"Sorted result: {values}",
            phase="result",
            state={"array": list(values), "sorted": True},
        )

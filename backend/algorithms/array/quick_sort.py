"""Quick sort with partition visualization."""
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
class QuickSortAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="quick_sort",
            category="array",
            description="Sort values using recursive partitioning",
            emoji="⚡",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated values"}
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n log n) average, O(n^2) worst",
            space_complexity="O(log n) average",
            use_cases=[
                "Fast in-place sorting",
                "Partitioning around pivots",
                "Teaching divide and conquer",
            ],
            pseudocode=(
                "function QuickSort(A, lo, hi):\n"
                "    if lo < hi:\n"
                "        p = partition(A, lo, hi)\n"
                "        QuickSort(A, lo, p - 1)\n"
                "        QuickSort(A, p + 1, hi)"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        values = _parse_values(params.get("values", ""))
        if not values:
            return

        def state(lo: int | None = None, hi: int | None = None, pivot: int | None = None) -> dict:
            result = {"array": list(values)}
            if lo is not None and hi is not None:
                result["range"] = [lo, hi]
            if pivot is not None:
                result["pivot_index"] = pivot
                result["pivot_value"] = values[pivot]
            return result

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Quick Sort", "items": [{"value": value} for value in values]},
            message=f"Initial array: {values}",
            phase="init",
            state=state(),
        )

        def partition(lo: int, hi: int) -> Generator[Step, None, int]:
            pivot = values[hi]
            i = lo - 1

            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": [hi], "state": "current"},
                message=f"Choose pivot {pivot} at index {hi}",
                phase="explore",
                state=state(lo, hi, hi),
            )

            for j in range(lo, hi):
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": [j, hi], "state": "compare"},
                    message=f"Compare {values[j]} with pivot {pivot}",
                    phase="explore",
                    state={**state(lo, hi, hi), "scan_index": j, "store_index": i + 1},
                )

                if values[j] <= pivot:
                    i += 1
                    if i != j:
                        values[i], values[j] = values[j], values[i]
                        yield Step(
                            action=StepAction.SWAP_ARRAY_ITEMS,
                            target_type="array",
                            target_id="main",
                            value={"i": i, "j": j, "state": "swapped"},
                            message=f"Move {values[i]} into the <= pivot region",
                            phase="relax",
                            state={**state(lo, hi, hi), "store_index": i},
                        )

            pivot_index = i + 1
            values[pivot_index], values[hi] = values[hi], values[pivot_index]
            yield Step(
                action=StepAction.SWAP_ARRAY_ITEMS,
                target_type="array",
                target_id="main",
                value={"i": pivot_index, "j": hi, "state": "swapped"},
                message=f"Place pivot at index {pivot_index}",
                phase="finalize",
                state=state(lo, hi, pivot_index),
            )

            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": [pivot_index], "state": "sorted"},
                message=f"Pivot {values[pivot_index]} is in final position",
                phase="finalize",
                state=state(lo, hi, pivot_index),
            )
            return pivot_index

        def quicksort(lo: int, hi: int) -> Generator[Step, None, None]:
            if lo >= hi:
                if lo == hi:
                    yield Step(
                        action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                        target_type="array",
                        target_id="main",
                        value={"indices": [lo], "state": "sorted"},
                        message=f"Single item at index {lo} is sorted",
                        phase="finalize",
                        state=state(lo, hi),
                    )
                return

            pivot_index = yield from partition(lo, hi)
            yield from quicksort(lo, pivot_index - 1)
            yield from quicksort(pivot_index + 1, hi)

        yield from quicksort(0, len(values) - 1)

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Quick Sort", "items": [{"value": value, "state": "sorted"} for value in values]},
            message=f"Sorted result: {values}",
            phase="result",
            state={"array": list(values), "sorted": True},
        )

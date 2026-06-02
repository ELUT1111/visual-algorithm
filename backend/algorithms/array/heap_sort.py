"""Heap sort with array visualization."""
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
class HeapSortAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="heap_sort",
            category="array",
            description="Sort values by building a max heap and extracting maxima",
            emoji="⛰️",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated values"}
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n log n)",
            space_complexity="O(1)",
            use_cases=["In-place sorting", "Priority queue intuition", "Heap property teaching"],
            pseudocode=(
                "function HeapSort(A):\n"
                "    build max heap\n"
                "    for end from n-1 down to 1:\n"
                "        swap A[0], A[end]\n"
                "        heapify root within A[0:end]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        values = _parse_values(params.get("values", ""))
        if not values:
            return

        def state(heap_size: int) -> dict:
            return {"array": list(values), "heap_size": heap_size, "sorted_tail": list(range(heap_size, len(values)))}

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Heap Sort", "items": [{"value": value} for value in values]},
            message=f"Initial array: {values}",
            phase="init",
            state=state(len(values)),
        )

        def heapify(heap_size: int, root: int) -> Generator[Step, None, None]:
            largest = root
            left = 2 * root + 1
            right = 2 * root + 2

            candidates = [idx for idx in (root, left, right) if idx < heap_size]
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": candidates, "state": "compare"},
                message=f"Heapify root {root}",
                phase="explore",
                state=state(heap_size),
            )

            if left < heap_size and values[left] > values[largest]:
                largest = left
            if right < heap_size and values[right] > values[largest]:
                largest = right

            if largest != root:
                values[root], values[largest] = values[largest], values[root]
                yield Step(
                    action=StepAction.SWAP_ARRAY_ITEMS,
                    target_type="array",
                    target_id="main",
                    value={"i": root, "j": largest, "state": "swapped"},
                    message=f"Swap {root} and {largest} to restore heap property",
                    phase="relax",
                    state=state(heap_size),
                )
                yield from heapify(heap_size, largest)

        n = len(values)
        for idx in range(n // 2 - 1, -1, -1):
            yield from heapify(n, idx)

        for end in range(n - 1, 0, -1):
            values[0], values[end] = values[end], values[0]
            yield Step(
                action=StepAction.SWAP_ARRAY_ITEMS,
                target_type="array",
                target_id="main",
                value={"i": 0, "j": end, "state": "swapped"},
                message=f"Move max value {values[end]} to sorted position {end}",
                phase="finalize",
                state=state(end),
            )
            yield from heapify(end, 0)

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Heap Sort", "items": [{"value": value, "state": "sorted"} for value in values]},
            message=f"Sorted result: {values}",
            phase="result",
            state={"array": list(values), "sorted": True},
        )

"""Bubble sort with array visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BubbleSortAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="bubble_sort",
            category="array",
            description="Sort values by repeatedly swapping adjacent out-of-order items",
            emoji="🫧",
            parameters=[
                {
                    "name": "values",
                    "type": "str",
                    "required": True,
                    "description": "Comma-separated numbers (e.g. 7,3,9,1,5)",
                }
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n^2)",
            space_complexity="O(1)",
            use_cases=[
                "Teaching adjacent swaps",
                "Understanding stable comparison sorting",
                "Small nearly-sorted arrays",
            ],
            pseudocode=(
                "function BubbleSort(A):\n"
                "    for i from 0 to n - 1:\n"
                "        swapped = false\n"
                "        for j from 0 to n - i - 2:\n"
                "            if A[j] > A[j + 1]:\n"
                "                swap A[j], A[j + 1]\n"
                "                swapped = true\n"
                "        if not swapped: break"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        values_str = params.get("values", "")
        if not values_str:
            return

        try:
            values = [int(v.strip()) for v in values_str.split(",") if v.strip()]
        except ValueError:
            values = [v.strip() for v in values_str.split(",") if v.strip()]

        if not values:
            return

        def array_state(i: int | None = None, j: int | None = None) -> dict:
            state = {"array": list(values)}
            if i is not None:
                state["pass"] = i + 1
            if j is not None:
                state["compare"] = [j, j + 1]
            return state

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Bubble Sort", "items": [{"value": v} for v in values]},
            message=f"Initial array: {values}",
            phase="init",
            state=array_state(),
        )

        n = len(values)
        for i in range(n):
            swapped = False

            for j in range(0, n - i - 1):
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": [j, j + 1], "state": "compare"},
                    message=f"Compare index {j} ({values[j]}) and {j + 1} ({values[j + 1]})",
                    phase="explore",
                    state=array_state(i, j),
                )

                if values[j] > values[j + 1]:
                    values[j], values[j + 1] = values[j + 1], values[j]
                    swapped = True
                    yield Step(
                        action=StepAction.SWAP_ARRAY_ITEMS,
                        target_type="array",
                        target_id="main",
                        value={"i": j, "j": j + 1, "state": "swapped"},
                        message=f"Swap positions {j} and {j + 1}: {values}",
                        phase="relax",
                        state=array_state(i, j),
                    )

                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": [], "state": ""},
                    message="",
                    phase="explore",
                    state=array_state(i, j),
                )

            sorted_index = n - i - 1
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": list(range(sorted_index, n)), "state": "sorted"},
                message=f"Position {sorted_index} is fixed",
                phase="finalize",
                state=array_state(i),
            )

            if not swapped:
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": list(range(0, sorted_index + 1)), "state": "sorted"},
                    message="No swaps in this pass; array is sorted",
                    phase="finalize",
                    state=array_state(i),
                )
                break

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Bubble Sort", "items": [{"value": v, "state": "sorted"} for v in values]},
            message=f"Sorted result: {values}",
            phase="result",
            state={"array": list(values), "sorted": True},
        )

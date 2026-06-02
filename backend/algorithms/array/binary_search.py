"""Binary search on a sorted array."""
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
class BinarySearchAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="binary_search",
            category="array",
            description="Search for a target in a sorted array",
            emoji="🎯",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Sorted comma-separated values"},
                {"name": "target", "type": "str", "required": True, "description": "Target value"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(log n)",
            space_complexity="O(1)",
            use_cases=["Fast lookup in sorted arrays", "Search boundaries", "Divide and conquer teaching"],
            pseudocode=(
                "function BinarySearch(A, target):\n"
                "    lo = 0; hi = len(A) - 1\n"
                "    while lo <= hi:\n"
                "        mid = (lo + hi) // 2\n"
                "        if A[mid] == target: return mid\n"
                "        if A[mid] < target: lo = mid + 1\n"
                "        else: hi = mid - 1"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        values = _parse_values(params.get("values", ""))
        if not values:
            return

        target_raw = str(params.get("target", "")).strip()
        try:
            target: int | str = int(target_raw)
        except ValueError:
            target = target_raw

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Binary Search", "items": [{"value": value} for value in values]},
            message=f"Search for {target}",
            phase="init",
            state={"array": list(values), "target": target},
        )

        lo, hi = 0, len(values) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": [lo, mid, hi], "state": "compare"},
                message=f"Check mid index {mid}: {values[mid]}",
                phase="explore",
                state={"low": lo, "mid": mid, "high": hi, "target": target},
            )

            if values[mid] == target:
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": [mid], "state": "sorted"},
                    message=f"Found {target} at index {mid}",
                    phase="result",
                    state={"found": True, "index": mid, "target": target},
                )
                return
            if values[mid] < target:
                lo = mid + 1
                direction = "right"
            else:
                hi = mid - 1
                direction = "left"

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="array",
                target_id="main",
                message=f"Target is to the {direction}; new range [{lo}, {hi}]",
                phase="relax",
                state={"low": lo, "high": hi, "target": target},
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="main",
            message=f"{target} not found",
            phase="result",
            state={"found": False, "index": -1, "target": target},
        )

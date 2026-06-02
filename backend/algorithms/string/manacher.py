"""Manacher longest palindromic substring visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _radii_table(transformed: str, radii: list[int]) -> list[dict]:
    return [{"index": idx, "char": char, "radius": radii[idx]} for idx, char in enumerate(transformed)]


@registry.register
class ManacherAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="manacher",
            category="string",
            description="Find the longest palindromic substring in linear time",
            emoji="🪞",
            parameters=[
                {"name": "text", "type": "str", "required": True, "description": "Text to scan"}
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n)",
            space_complexity="O(n)",
            use_cases=[
                "Longest palindromic substring",
                "Linear string preprocessing",
                "Palindrome detection",
                "Mirror symmetry teaching",
            ],
            pseudocode=(
                "function Manacher(text):\n"
                "    transform text with separators\n"
                "    for each center i:\n"
                "        seed radius from mirror if inside right boundary\n"
                "        expand while characters match\n"
                "        update center and right boundary"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = str(params.get("text", ""))
        if not text:
            return

        transformed = "^#" + "#".join(text) + "#$"
        radii = [0] * len(transformed)
        center = 0
        right = 0
        best_center = 0
        best_radius = 0

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="manacher",
            value={
                "title": f"Manacher: '{text}'",
                "items": [{"value": char, "meta": str(idx)} for idx, char in enumerate(transformed)],
            },
            message=f"Transform text to '{transformed}'",
            phase="init",
            state={"text": text, "transformed": transformed, "radii_table": _radii_table(transformed, radii)},
        )

        for i in range(1, len(transformed) - 1):
            mirror = 2 * center - i
            if i < right:
                radii[i] = min(right - i, radii[mirror])

            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="manacher",
                value={"indices": [i], "state": "compare"},
                message=f"Use center {i}, mirror {mirror}, boundary {right}",
                phase="explore",
                state={
                    "center": center,
                    "right": right,
                    "index": i,
                    "mirror": mirror,
                    "seed_radius": radii[i],
                    "radii_table": _radii_table(transformed, radii),
                },
            )

            while transformed[i + 1 + radii[i]] == transformed[i - 1 - radii[i]]:
                radii[i] += 1

            if i + radii[i] > right:
                center = i
                right = i + radii[i]

            if radii[i] > best_radius:
                best_center = i
                best_radius = radii[i]

            yield Step(
                action=StepAction.UPDATE_ARRAY_ITEM,
                target_type="array",
                target_id="manacher",
                value={"index": i, "value": transformed[i], "state": "updated", "meta": f"r={radii[i]}"},
                message=f"Radius at {i} is {radii[i]}",
                phase="relax",
                state={
                    "center": center,
                    "right": right,
                    "best_center": best_center,
                    "best_radius": best_radius,
                    "radii_table": _radii_table(transformed, radii),
                },
            )

        start = (best_center - best_radius) // 2
        palindrome = text[start:start + best_radius]

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="manacher",
            message=f"Longest palindrome is '{palindrome}'",
            phase="result",
            state={
                "longest_palindrome": palindrome,
                "start": start,
                "length": best_radius,
                "radii_table": _radii_table(transformed, radii),
            },
        )

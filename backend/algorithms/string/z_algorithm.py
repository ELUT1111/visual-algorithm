"""Z algorithm string matching visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _separator(text: str, pattern: str) -> str:
    for candidate in ("$", "#", "\x1f", "|"):
        if candidate not in text and candidate not in pattern:
            return candidate
    return "\x00"


def _z_table(combined: str, z: list[int]) -> list[dict]:
    return [
        {"index": idx, "char": char, "z": z[idx]}
        for idx, char in enumerate(combined)
    ]


@registry.register
class ZAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="z_algorithm",
            category="string",
            description="Find pattern occurrences by computing the Z array",
            emoji="Ⓩ",
            parameters=[
                {"name": "text", "type": "str", "required": True, "description": "Text to search"},
                {"name": "pattern", "type": "str", "required": True, "description": "Pattern to find"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n + m)",
            space_complexity="O(n + m)",
            use_cases=[
                "Linear-time substring search",
                "Prefix analysis",
                "String preprocessing education",
                "Competitive programming",
            ],
            pseudocode=(
                "function ZSearch(text, pattern):\n"
                "    s = pattern + separator + text\n"
                "    compute Z values with a [left, right] box\n"
                "    every index with Z[i] == len(pattern) is a match"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = str(params.get("text", ""))
        pattern = str(params.get("pattern", ""))
        if not text or not pattern:
            return

        sep = _separator(text, pattern)
        combined = pattern + sep + text
        z = [0 for _ in combined]
        left = 0
        right = 0
        offset = len(pattern) + 1
        matches: list[int] = []

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={
                "title": f"Z Algorithm: '{pattern}'",
                "items": [{"value": char, "meta": str(idx)} for idx, char in enumerate(combined)],
            },
            message=f"Build combined string pattern + separator + text: '{combined}'",
            phase="init",
            state={
                "text": text,
                "pattern": pattern,
                "combined": combined,
                "separator": sep,
                "z_table": _z_table(combined, z),
                "matches": [],
            },
        )

        for i in range(1, len(combined)):
            if i <= right:
                z[i] = min(right - i + 1, z[i - left])

            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": [i], "state": "compare"},
                message=f"Compute Z[{i}] with current box [{left}, {right}]",
                phase="explore",
                state={
                    "index": i,
                    "z_box": {"left": left, "right": right},
                    "seed_value": z[i],
                    "z_table": _z_table(combined, z),
                    "matches": list(matches),
                },
            )

            while i + z[i] < len(combined) and combined[z[i]] == combined[i + z[i]]:
                z[i] += 1

            if i + z[i] - 1 > right:
                left = i
                right = i + z[i] - 1

            if i >= offset and z[i] >= len(pattern):
                match_start = i - offset
                matches.append(match_start)
                state = "sorted"
                message = f"Pattern match at text index {match_start}"
            else:
                state = "swapped" if z[i] else "current"
                message = f"Set Z[{i}] = {z[i]}"

            yield Step(
                action=StepAction.UPDATE_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"index": i, "value": combined[i], "state": state, "meta": f"z={z[i]}"},
                message=message,
                phase="relax" if state != "sorted" else "result",
                state={
                    "index": i,
                    "z_value": z[i],
                    "z_box": {"left": left, "right": right},
                    "z_table": _z_table(combined, z),
                    "matches": list(matches),
                },
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="main",
            message=f"Z algorithm complete. Matches at indices: {matches}",
            phase="result",
            state={"matches": matches, "count": len(matches), "z_table": _z_table(combined, z)},
        )

"""Boyer-Moore string matching using the bad-character rule."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _bad_char_table(pattern: str) -> dict[str, int]:
    return {char: idx for idx, char in enumerate(pattern)}


@registry.register
class BoyerMooreAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="boyer_moore",
            category="string",
            description="Find pattern occurrences by scanning windows from right to left",
            emoji="↩️",
            parameters=[
                {"name": "text", "type": "str", "required": True, "description": "Text to search"},
                {"name": "pattern", "type": "str", "required": True, "description": "Pattern to find"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(nm) worst, sublinear often",
            space_complexity="O(k)",
            use_cases=[
                "Text editor search",
                "Large text scanning",
                "Right-to-left matching education",
                "Search engine internals",
            ],
            pseudocode=(
                "function BoyerMoore(text, pattern):\n"
                "    last = bad-character table for pattern\n"
                "    shift = 0\n"
                "    while shift <= n - m:\n"
                "        compare pattern from right to left\n"
                "        if match: report shift; shift += 1\n"
                "        else: shift by max(1, j - last[text[shift+j]])"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = str(params.get("text", ""))
        pattern = str(params.get("pattern", ""))
        if not text or not pattern or len(pattern) > len(text):
            return

        n = len(text)
        m = len(pattern)
        bad_char = _bad_char_table(pattern)
        table_rows = [{"char": char, "last_index": idx} for char, idx in sorted(bad_char.items())]

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={
                "title": f"Boyer-Moore Search: '{pattern}'",
                "items": [{"value": char, "meta": str(idx)} for idx, char in enumerate(text)],
            },
            message=f"Built bad-character table for pattern '{pattern}'",
            phase="init",
            state={"text": text, "pattern": pattern, "bad_char_table": table_rows, "matches": []},
        )

        matches: list[int] = []
        shift = 0
        while shift <= n - m:
            window_indices = list(range(shift, shift + m))
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": window_indices, "state": "compare"},
                message=f"Align pattern at text index {shift}",
                phase="explore",
                state={
                    "shift": shift,
                    "window": {"start": shift, "end": shift + m - 1, "text": text[shift:shift + m]},
                    "bad_char_table": table_rows,
                    "matches": list(matches),
                },
            )

            j = m - 1
            while j >= 0 and pattern[j] == text[shift + j]:
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": [shift + j], "state": "current"},
                    message=f"Match from right: pattern[{j}]='{pattern[j]}'",
                    phase="explore",
                    state={
                        "shift": shift,
                        "pattern_index": j,
                        "text_index": shift + j,
                        "matched_suffix": pattern[j:],
                        "matches": list(matches),
                    },
                )
                j -= 1

            if j < 0:
                matches.append(shift)
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": window_indices, "state": "sorted"},
                    message=f"Match found at index {shift}",
                    phase="result",
                    state={"match_start": shift, "match_range": window_indices, "matches": list(matches)},
                )
                shift += 1
                continue

            bad = text[shift + j]
            last_seen = bad_char.get(bad, -1)
            jump = max(1, j - last_seen)
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="array",
                target_id="main",
                message=f"Mismatch on '{bad}'; shift by {jump}",
                phase="relax",
                state={
                    "shift": shift,
                    "mismatch": {
                        "pattern_index": j,
                        "text_index": shift + j,
                        "text_char": bad,
                        "pattern_char": pattern[j],
                    },
                    "bad_char_last_seen": last_seen,
                    "next_shift": shift + jump,
                    "matches": list(matches),
                },
            )
            shift += jump

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="main",
            message=f"Boyer-Moore complete. Matches at indices: {matches}",
            phase="result",
            state={"matches": matches, "count": len(matches), "bad_char_table": table_rows},
        )

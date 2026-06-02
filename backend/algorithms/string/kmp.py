"""Knuth-Morris-Pratt string matching visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _lps_table(pattern: str, lps: list[int]) -> list[dict]:
    return [
        {"index": idx, "char": char, "lps": lps[idx]}
        for idx, char in enumerate(pattern)
    ]


@registry.register
class KMPAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="kmp",
            category="string",
            description="Find pattern occurrences using the KMP prefix table",
            emoji="🔤",
            parameters=[
                {"name": "text", "type": "str", "required": True, "description": "Text to search"},
                {"name": "pattern", "type": "str", "required": True, "description": "Pattern to find"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n + m)",
            space_complexity="O(m)",
            use_cases=[
                "Fast substring search",
                "Text editors and search tools",
                "Log scanning",
                "Pattern matching education",
            ],
            pseudocode=(
                "function KMP(text, pattern):\n"
                "    lps = build longest-prefix-suffix table for pattern\n"
                "    i = j = 0\n"
                "    while i < len(text):\n"
                "        if text[i] == pattern[j]: i++, j++\n"
                "        if j == len(pattern): report match; j = lps[j-1]\n"
                "        else if mismatch and j > 0: j = lps[j-1]\n"
                "        else i++"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = str(params.get("text", ""))
        pattern = str(params.get("pattern", ""))
        if not text or not pattern:
            return

        lps = [0 for _ in pattern]
        length = 0
        idx = 1

        while idx < len(pattern):
            if pattern[idx] == pattern[length]:
                length += 1
                lps[idx] = length
                idx += 1
            elif length > 0:
                length = lps[length - 1]
            else:
                lps[idx] = 0
                idx += 1

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={
                "title": f"KMP Search: '{pattern}'",
                "items": [{"value": ch, "meta": str(idx)} for idx, ch in enumerate(text)],
            },
            message=f"Built LPS table for pattern '{pattern}': {lps}",
            phase="init",
            state={
                "text": text,
                "pattern": pattern,
                "lps": lps,
                "lps_table": _lps_table(pattern, lps),
                "matches": [],
            },
        )

        matches: list[int] = []
        i = 0
        j = 0
        while i < len(text):
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": [i], "state": "compare"},
                message=f"Compare text[{i}]='{text[i]}' with pattern[{j}]='{pattern[j]}'",
                phase="explore",
                state={
                    "text_index": i,
                    "pattern_index": j,
                    "text_char": text[i],
                    "pattern_char": pattern[j],
                    "matched_prefix": pattern[:j],
                    "active_window": {
                        "start": i - j,
                        "end": i,
                        "text": text[max(0, i - j): i + 1],
                    },
                    "lps_table": _lps_table(pattern, lps),
                    "matches": list(matches),
                },
            )

            if text[i] == pattern[j]:
                i += 1
                j += 1

                if j == len(pattern):
                    start = i - j
                    matches.append(start)
                    match_indices = list(range(start, i))
                    yield Step(
                        action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                        target_type="array",
                        target_id="main",
                        value={"indices": match_indices, "state": "sorted"},
                        message=f"Match found at index {start}",
                        phase="result",
                        state={
                            "text_index": i,
                            "pattern_index": j,
                            "match_start": start,
                            "match_range": match_indices,
                            "matched_text": text[start:i],
                            "lps_table": _lps_table(pattern, lps),
                            "matches": list(matches),
                        },
                    )
                    j = lps[j - 1]
            else:
                if j > 0:
                    previous = j
                    j = lps[j - 1]
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="array",
                        target_id="main",
                        message=f"Mismatch; fallback pattern index from {previous} to {j}",
                        phase="relax",
                        state={
                            "text_index": i,
                            "pattern_index": j,
                            "fallback": {
                                "from": previous,
                                "to": j,
                                "reason": f"lps[{previous - 1}]",
                            },
                            "lps_table": _lps_table(pattern, lps),
                            "matches": list(matches),
                        },
                    )
                else:
                    i += 1

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="main",
            message=f"KMP complete. Matches at indices: {matches}",
            phase="result",
            state={
                "matches": matches,
                "count": len(matches),
                "lps": lps,
                "lps_table": _lps_table(pattern, lps),
            },
        )

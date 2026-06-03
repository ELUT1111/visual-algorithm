"""Suffix array construction and pattern lookup visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _items(text: str, suffix_array: list[int], ranks: list[int]) -> list[dict]:
    return [
        {"value": index, "meta": f"rank={ranks[index]} {text[index:]}"}
        for index in suffix_array
    ]


@registry.register
class SuffixArrayAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="suffix_array",
            category="string",
            description="Build a suffix array with doubling ranks and search a pattern",
            emoji="SA",
            parameters=[
                {"name": "text", "type": "str", "required": True, "description": "Text to index"},
                {"name": "pattern", "type": "str", "required": False, "default": "", "description": "Optional pattern to search"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            use_cases=[
                "Full-text search",
                "Substring queries",
                "Longest repeated substring",
                "String indexing",
            ],
            pseudocode=(
                "rank suffixes by first character\n"
                "for k = 1, 2, 4, ...:\n"
                "    sort suffixes by (rank[i], rank[i+k])\n"
                "    assign new ranks\n"
                "binary search the suffix array for pattern matches"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = str(params.get("text", ""))
        pattern = str(params.get("pattern", ""))
        if not text:
            return

        n = len(text)
        suffix_array = list(range(n))
        ranks = [ord(char) for char in text]
        k = 1

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="suffix_array",
            value={"title": "Suffix Array", "items": _items(text, suffix_array, ranks)},
            message=f"Initialize suffixes for '{text}'",
            phase="init",
            state={"text": text, "suffix_array": suffix_array, "ranks": ranks},
        )

        while k < n:
            suffix_array.sort(key=lambda idx: (ranks[idx], ranks[idx + k] if idx + k < n else -1))
            new_ranks = [0] * n
            for pos in range(1, n):
                prev = suffix_array[pos - 1]
                curr = suffix_array[pos]
                prev_key = (ranks[prev], ranks[prev + k] if prev + k < n else -1)
                curr_key = (ranks[curr], ranks[curr + k] if curr + k < n else -1)
                new_ranks[curr] = new_ranks[prev] + (1 if curr_key != prev_key else 0)
            ranks = new_ranks

            yield Step(
                action=StepAction.RENDER_ARRAY,
                target_type="array",
                target_id="suffix_array",
                value={"title": f"Suffix Array k={k}", "items": _items(text, suffix_array, ranks)},
                message=f"Sort suffixes by 2*{k} character prefixes",
                phase="relax",
                state={"text": text, "k": k, "suffix_array": list(suffix_array), "ranks": list(ranks)},
            )

            if ranks[suffix_array[-1]] == n - 1:
                break
            k *= 2

        matches: list[int] = []
        if pattern:
            lo, hi = 0, n
            while lo < hi:
                mid = (lo + hi) // 2
                suffix = text[suffix_array[mid]:]
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="suffix_array",
                    value={"indices": [mid], "state": "compare"},
                    message=f"Binary search compare '{pattern}' with suffix '{suffix}'",
                    phase="explore",
                    state={"pattern": pattern, "low": lo, "mid": mid, "high": hi, "suffix": suffix},
                )
                if suffix < pattern:
                    lo = mid + 1
                else:
                    hi = mid
            start = lo

            lo, hi = 0, n
            upper = pattern + chr(0x10FFFF)
            while lo < hi:
                mid = (lo + hi) // 2
                suffix = text[suffix_array[mid]:]
                if suffix < upper:
                    lo = mid + 1
                else:
                    hi = mid
            end = lo
            matches = sorted(index for index in suffix_array[start:end] if text.startswith(pattern, index))
            if matches:
                positions = [suffix_array.index(index) for index in matches]
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="suffix_array",
                    value={"indices": positions, "state": "sorted"},
                    message=f"Pattern '{pattern}' occurs at indices {matches}",
                    phase="result",
                    state={"pattern": pattern, "matches": matches, "suffix_array": list(suffix_array), "ranks": list(ranks)},
                )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="suffix_array",
            message=f"Suffix array complete. Matches: {matches}",
            phase="result",
            state={"text": text, "pattern": pattern, "suffix_array": suffix_array, "ranks": ranks, "matches": matches},
        )

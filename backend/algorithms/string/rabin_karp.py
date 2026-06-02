"""Rabin-Karp string matching with rolling hash visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _window_text(text: str, start: int, size: int) -> str:
    return text[start:start + size]


@registry.register
class RabinKarpAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="rabin_karp",
            category="string",
            description="Find pattern occurrences with a rolling hash",
            emoji="🔎",
            parameters=[
                {"name": "text", "type": "str", "required": True, "description": "Text to search"},
                {"name": "pattern", "type": "str", "required": True, "description": "Pattern to find"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n + m) average, O(nm) worst",
            space_complexity="O(1)",
            use_cases=[
                "Fast substring search",
                "Plagiarism detection",
                "Multi-pattern search foundations",
                "Rolling hash education",
            ],
            pseudocode=(
                "function RabinKarp(text, pattern):\n"
                "    pattern_hash = hash(pattern)\n"
                "    window_hash = hash(text[0:m])\n"
                "    for each window in text:\n"
                "        if hashes match, verify characters\n"
                "        roll the hash to the next window"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = str(params.get("text", ""))
        pattern = str(params.get("pattern", ""))
        if not text or not pattern or len(pattern) > len(text):
            return

        base = 256
        mod = 101
        n = len(text)
        m = len(pattern)
        high_order = pow(base, m - 1, mod)

        pattern_hash = 0
        window_hash = 0
        for idx in range(m):
            pattern_hash = (base * pattern_hash + ord(pattern[idx])) % mod
            window_hash = (base * window_hash + ord(text[idx])) % mod

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={
                "title": f"Rabin-Karp Search: '{pattern}'",
                "items": [{"value": char, "meta": str(idx)} for idx, char in enumerate(text)],
            },
            message=f"Pattern hash is {pattern_hash}; first window hash is {window_hash}",
            phase="init",
            state={
                "text": text,
                "pattern": pattern,
                "base": base,
                "mod": mod,
                "pattern_hash": pattern_hash,
                "window_hash": window_hash,
                "matches": [],
            },
        )

        matches: list[int] = []
        for start in range(n - m + 1):
            window = _window_text(text, start, m)
            indices = list(range(start, start + m))
            hash_match = pattern_hash == window_hash
            exact_match = hash_match and window == pattern

            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="main",
                value={"indices": indices, "state": "compare"},
                message=f"Window [{start}, {start + m - 1}] hash {window_hash}",
                phase="explore",
                state={
                    "window": {"start": start, "end": start + m - 1, "text": window},
                    "pattern_hash": pattern_hash,
                    "window_hash": window_hash,
                    "hash_match": hash_match,
                    "exact_match": exact_match,
                    "matches": list(matches),
                },
            )

            if exact_match:
                matches.append(start)
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": indices, "state": "sorted"},
                    message=f"Verified match at index {start}",
                    phase="result",
                    state={
                        "match_start": start,
                        "match_range": indices,
                        "matches": list(matches),
                    },
                )
            elif hash_match:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="array",
                    target_id="main",
                    message=f"Hash collision at index {start}; characters differ",
                    phase="relax",
                    state={
                        "window": {"start": start, "end": start + m - 1, "text": window},
                        "pattern": pattern,
                        "matches": list(matches),
                    },
                )

            if start < n - m:
                outgoing = text[start]
                incoming = text[start + m]
                next_hash = (
                    (window_hash - ord(outgoing) * high_order) * base + ord(incoming)
                ) % mod
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="array",
                    target_id="main",
                    message=f"Roll hash: remove '{outgoing}', add '{incoming}' -> {next_hash}",
                    phase="relax",
                    state={
                        "rolling_hash": {
                            "from_start": start,
                            "to_start": start + 1,
                            "outgoing": outgoing,
                            "incoming": incoming,
                            "previous_hash": window_hash,
                            "next_hash": next_hash,
                        },
                        "matches": list(matches),
                    },
                )
                window_hash = next_hash

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="main",
            message=f"Rabin-Karp complete. Matches at indices: {matches}",
            phase="result",
            state={"matches": matches, "count": len(matches), "pattern_hash": pattern_hash},
        )

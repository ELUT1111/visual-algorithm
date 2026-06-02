"""Word Break dynamic programming visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _dp_table(text: str, dp: list[bool], prev: list[int | None]) -> list[dict]:
    return [
        {
            "index": idx,
            "prefix": text[:idx],
            "reachable": dp[idx],
            "previous": prev[idx],
        }
        for idx in range(len(dp))
    ]


@registry.register
class WordBreakAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="word_break",
            category="dp",
            description="Decide whether text can be segmented into dictionary words",
            emoji="🧾",
            parameters=[
                {"name": "text", "type": "str", "required": True, "description": "Text to segment"},
                {"name": "words", "type": "str", "required": True, "description": "Comma-separated dictionary words"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n^2 * k)",
            space_complexity="O(n)",
            use_cases=[
                "Text segmentation",
                "Tokenizer demonstrations",
                "Dictionary based parsing",
                "Boolean dynamic programming",
            ],
            pseudocode=(
                "function WordBreak(text, words):\n"
                "    dp[0] = true\n"
                "    for i from 1 to n:\n"
                "        for j from 0 to i-1:\n"
                "            if dp[j] and text[j:i] in words:\n"
                "                dp[i] = true"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = str(params.get("text", ""))
        words = {word.strip() for word in str(params.get("words", "")).split(",") if word.strip()}
        if not text or not words:
            return

        n = len(text)
        dp = [False] * (n + 1)
        prev: list[int | None] = [None] * (n + 1)
        dp[0] = True

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="word-break",
            value={
                "title": f"Word Break: '{text}'",
                "items": [{"value": idx, "meta": "T" if dp[idx] else "F"} for idx in range(n + 1)],
            },
            message="Initialize dp[0] = true",
            phase="init",
            state={"text": text, "words": sorted(words), "dp_table": _dp_table(text, dp, prev)},
        )

        for i in range(1, n + 1):
            for j in range(i):
                segment = text[j:i]
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="word-break",
                    value={"indices": [j, i], "state": "compare"},
                    message=f"Check segment '{segment}' from {j} to {i}",
                    phase="explore",
                    state={
                        "i": i,
                        "j": j,
                        "segment": segment,
                        "prefix_reachable": dp[j],
                        "in_dictionary": segment in words,
                        "dp_table": _dp_table(text, dp, prev),
                    },
                )

                if dp[j] and segment in words:
                    dp[i] = True
                    prev[i] = j
                    yield Step(
                        action=StepAction.UPDATE_ARRAY_ITEM,
                        target_type="array",
                        target_id="word-break",
                        value={"index": i, "value": i, "state": "updated", "meta": "T"},
                        message=f"dp[{i}] = true using '{segment}'",
                        phase="relax",
                        state={"i": i, "word": segment, "dp_table": _dp_table(text, dp, prev)},
                    )
                    break

            if not dp[i]:
                yield Step(
                    action=StepAction.UPDATE_ARRAY_ITEM,
                    target_type="array",
                    target_id="word-break",
                    value={"index": i, "value": i, "state": "current", "meta": "F"},
                    message=f"No segmentation reaches prefix '{text[:i]}'",
                    phase="finalize",
                    state={"i": i, "dp_table": _dp_table(text, dp, prev)},
                )

        segmentation: list[str] = []
        cursor = n
        while cursor > 0 and prev[cursor] is not None:
            start = prev[cursor]
            segmentation.append(text[start:cursor])
            cursor = start
        segmentation.reverse()

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="array",
            target_id="word-break",
            message=f"Word break {'possible' if dp[n] else 'not possible'}",
            phase="result",
            state={
                "can_segment": dp[n],
                "segmentation": segmentation,
                "dp_table": _dp_table(text, dp, prev),
            },
        )

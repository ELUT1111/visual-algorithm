"""Longest Common Subsequence dynamic programming visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class LCSAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="lcs",
            category="dp",
            description="Longest common subsequence via dynamic programming matrix",
            emoji="🧬",
            parameters=[
                {"name": "text_a", "type": "str", "required": True, "description": "First string"},
                {"name": "text_b", "type": "str", "required": True, "description": "Second string"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="matrix",
            time_complexity="O(mn)",
            space_complexity="O(mn)",
            use_cases=[
                "Diff tools",
                "Version control merge analysis",
                "Bioinformatics sequence comparison",
                "Text similarity",
            ],
            pseudocode=(
                "function LCS(a, b):\n"
                "    dp = zero matrix of size (len(a)+1) x (len(b)+1)\n"
                "    for i from 1 to len(a):\n"
                "        for j from 1 to len(b):\n"
                "            if a[i-1] == b[j-1]: dp[i][j] = dp[i-1][j-1] + 1\n"
                "            else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n"
                "    return dp[len(a)][len(b)]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text_a = params.get("text_a", "")
        text_b = params.get("text_b", "")
        if not text_a or not text_b:
            return

        rows = ["∅"] + list(text_a)
        cols = ["∅"] + list(text_b)
        dp = [[0 for _ in cols] for _ in rows]

        def matrix_payload(title: str = "LCS Matrix", highlights: list[dict] | None = None) -> dict:
            return {
                "title": title,
                "rows": rows,
                "columns": cols,
                "values": [[value for value in row] for row in dp],
                "highlights": highlights or [],
            }

        yield Step(
            action=StepAction.RENDER_MATRIX,
            target_type="matrix",
            target_id="lcs",
            value=matrix_payload(),
            message=f"Build LCS table for '{text_a}' and '{text_b}'",
            phase="init",
            state={"text_a": text_a, "text_b": text_b},
        )

        for i in range(1, len(rows)):
            for j in range(1, len(cols)):
                a_char = text_a[i - 1]
                b_char = text_b[j - 1]

                yield Step(
                    action=StepAction.HIGHLIGHT_MATRIX_CELL,
                    target_type="matrix",
                    target_id="lcs",
                    value={"row": i, "col": j, "state": "current"},
                    message=f"Compare '{a_char}' with '{b_char}'",
                    phase="explore",
                    state={"i": i, "j": j, "a_char": a_char, "b_char": b_char},
                )

                if a_char == b_char:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    msg = f"Match: dp[{i}][{j}] = dp[{i - 1}][{j - 1}] + 1 = {dp[i][j]}"
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                    msg = f"No match: dp[{i}][{j}] = max({dp[i - 1][j]}, {dp[i][j - 1]}) = {dp[i][j]}"

                yield Step(
                    action=StepAction.UPDATE_MATRIX_CELL,
                    target_type="matrix",
                    target_id="lcs",
                    value={"row": i, "col": j, "value": dp[i][j], "state": "updated"},
                    message=msg,
                    phase="relax",
                    state={"i": i, "j": j, "value": dp[i][j]},
                )

        i, j = len(text_a), len(text_b)
        lcs_chars: list[str] = []
        path: list[dict] = []
        backtrack_path: list[dict] = []
        while i > 0 and j > 0:
            path.append({"row": i, "col": j, "state": "path"})
            if text_a[i - 1] == text_b[j - 1]:
                backtrack_path.append(
                    {
                        "row": i,
                        "col": j,
                        "a_char": text_a[i - 1],
                        "b_char": text_b[j - 1],
                        "decision": "take diagonal",
                        "lcs_char": text_a[i - 1],
                    }
                )
                lcs_chars.append(text_a[i - 1])
                i -= 1
                j -= 1
            elif dp[i - 1][j] >= dp[i][j - 1]:
                backtrack_path.append(
                    {
                        "row": i,
                        "col": j,
                        "a_char": text_a[i - 1],
                        "b_char": text_b[j - 1],
                        "decision": "move up",
                    }
                )
                i -= 1
            else:
                backtrack_path.append(
                    {
                        "row": i,
                        "col": j,
                        "a_char": text_a[i - 1],
                        "b_char": text_b[j - 1],
                        "decision": "move left",
                    }
                )
                j -= 1

        path.append({"row": i, "col": j, "state": "path"})
        backtrack_path.reverse()
        lcs_value = "".join(reversed(lcs_chars))

        yield Step(
            action=StepAction.HIGHLIGHT_MATRIX_CELL,
            target_type="matrix",
            target_id="lcs",
            value={"cells": path, "state": "path"},
            message=f"LCS result: '{lcs_value}' (length {dp[-1][-1]})",
            phase="result",
            state={
                "lcs": lcs_value,
                "length": dp[-1][-1],
                "backtrack_path": backtrack_path,
                "path_cells": list(reversed(path)),
            },
        )

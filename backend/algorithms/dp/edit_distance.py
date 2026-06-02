"""Edit distance dynamic programming visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class EditDistanceAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="edit_distance",
            category="dp",
            description="Compute Levenshtein edit distance with a dynamic programming matrix",
            emoji="✏️",
            parameters=[
                {"name": "text_a", "type": "str", "required": True, "description": "Source string"},
                {"name": "text_b", "type": "str", "required": True, "description": "Target string"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="matrix",
            time_complexity="O(mn)",
            space_complexity="O(mn)",
            use_cases=[
                "Spell checking",
                "Fuzzy search",
                "Text similarity",
                "DNA sequence comparison",
            ],
            pseudocode=(
                "function EditDistance(a, b):\n"
                "    dp[i][0] = i and dp[0][j] = j\n"
                "    for i from 1 to len(a):\n"
                "        for j from 1 to len(b):\n"
                "            cost = 0 if a[i-1] == b[j-1] else 1\n"
                "            dp[i][j] = min(delete, insert, substitute)\n"
                "    return dp[len(a)][len(b)]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text_a = str(params.get("text_a", ""))
        text_b = str(params.get("text_b", ""))
        if not text_a and not text_b:
            return

        rows = ["∅"] + list(text_a)
        cols = ["∅"] + list(text_b)
        dp = [[0 for _ in cols] for _ in rows]

        def matrix_payload(title: str = "Edit Distance") -> dict:
            return {
                "title": title,
                "rows": rows,
                "columns": cols,
                "values": [[value for value in row] for row in dp],
            }

        yield Step(
            action=StepAction.RENDER_MATRIX,
            target_type="matrix",
            target_id="edit_distance",
            value=matrix_payload(),
            message=f"Build edit-distance table from '{text_a}' to '{text_b}'",
            phase="init",
            state={"text_a": text_a, "text_b": text_b},
        )

        for i in range(1, len(rows)):
            dp[i][0] = i
            yield Step(
                action=StepAction.UPDATE_MATRIX_CELL,
                target_type="matrix",
                target_id="edit_distance",
                value={"row": i, "col": 0, "value": i, "state": "updated"},
                message=f"Base case: delete {i} character(s) to reach empty target",
                phase="init",
                state={"row": i, "col": 0, "value": i},
            )

        for j in range(1, len(cols)):
            dp[0][j] = j
            yield Step(
                action=StepAction.UPDATE_MATRIX_CELL,
                target_type="matrix",
                target_id="edit_distance",
                value={"row": 0, "col": j, "value": j, "state": "updated"},
                message=f"Base case: insert {j} character(s) from empty source",
                phase="init",
                state={"row": 0, "col": j, "value": j},
            )

        for i in range(1, len(rows)):
            for j in range(1, len(cols)):
                a_char = text_a[i - 1]
                b_char = text_b[j - 1]
                cost = 0 if a_char == b_char else 1

                yield Step(
                    action=StepAction.HIGHLIGHT_MATRIX_CELL,
                    target_type="matrix",
                    target_id="edit_distance",
                    value={"row": i, "col": j, "state": "current"},
                    message=f"Compare '{a_char}' with '{b_char}'",
                    phase="explore",
                    state={"i": i, "j": j, "a_char": a_char, "b_char": b_char, "cost": cost},
                )

                delete_cost = dp[i - 1][j] + 1
                insert_cost = dp[i][j - 1] + 1
                replace_cost = dp[i - 1][j - 1] + cost
                dp[i][j] = min(delete_cost, insert_cost, replace_cost)

                yield Step(
                    action=StepAction.UPDATE_MATRIX_CELL,
                    target_type="matrix",
                    target_id="edit_distance",
                    value={"row": i, "col": j, "value": dp[i][j], "state": "updated"},
                    message=(
                        f"dp[{i}][{j}] = min(delete {delete_cost}, "
                        f"insert {insert_cost}, replace {replace_cost}) = {dp[i][j]}"
                    ),
                    phase="relax",
                    state={
                        "i": i,
                        "j": j,
                        "delete": delete_cost,
                        "insert": insert_cost,
                        "replace": replace_cost,
                        "value": dp[i][j],
                    },
                )

        i = len(text_a)
        j = len(text_b)
        backtrack_path: list[dict] = []
        edit_script: list[dict] = []
        path_cells: list[dict] = []

        while i > 0 or j > 0:
            path_cells.append({"row": i, "col": j, "state": "path"})

            if i > 0 and j > 0:
                cost = 0 if text_a[i - 1] == text_b[j - 1] else 1
                if dp[i][j] == dp[i - 1][j - 1] + cost:
                    operation = "match" if cost == 0 else "replace"
                    step = {
                        "row": i,
                        "col": j,
                        "operation": operation,
                        "from_char": text_a[i - 1],
                        "to_char": text_b[j - 1],
                        "cost": cost,
                        "next": {"row": i - 1, "col": j - 1},
                    }
                    backtrack_path.append(step)
                    if operation != "match":
                        edit_script.append(step)
                    i -= 1
                    j -= 1
                    continue

            if i > 0 and dp[i][j] == dp[i - 1][j] + 1:
                step = {
                    "row": i,
                    "col": j,
                    "operation": "delete",
                    "from_char": text_a[i - 1],
                    "to_char": "",
                    "cost": 1,
                    "next": {"row": i - 1, "col": j},
                }
                backtrack_path.append(step)
                edit_script.append(step)
                i -= 1
            else:
                step = {
                    "row": i,
                    "col": j,
                    "operation": "insert",
                    "from_char": "",
                    "to_char": text_b[j - 1],
                    "cost": 1,
                    "next": {"row": i, "col": j - 1},
                }
                backtrack_path.append(step)
                edit_script.append(step)
                j -= 1

        path_cells.append({"row": 0, "col": 0, "state": "path"})
        backtrack_path.reverse()
        edit_script.reverse()
        path_cells.reverse()

        yield Step(
            action=StepAction.HIGHLIGHT_MATRIX_CELL,
            target_type="matrix",
            target_id="edit_distance",
            value={"cells": path_cells, "state": "path"},
            message=f"Edit distance is {dp[-1][-1]}",
            phase="result",
            state={
                "distance": dp[-1][-1],
                "text_a": text_a,
                "text_b": text_b,
                "edit_script": edit_script,
                "backtrack_path": backtrack_path,
                "path_cells": path_cells,
            },
        )

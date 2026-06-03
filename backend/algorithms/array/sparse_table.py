"""Sparse table for static range minimum/maximum queries."""
from __future__ import annotations

from math import log2
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_values(raw: str) -> list[int]:
    return [int(item.strip()) for item in raw.split(",") if item.strip()]


@registry.register
class SparseTableAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="sparse_table",
            category="array",
            description="Preprocess a static array for O(1) idempotent range queries",
            emoji="ST",
            parameters=[
                {"name": "values", "type": "str", "required": True, "description": "Comma-separated integers"},
                {"name": "query_left", "type": "int", "required": False, "default": "1", "description": "0-based query left index"},
                {"name": "query_right", "type": "int", "required": False, "default": "4", "description": "0-based query right index"},
                {
                    "name": "operation",
                    "type": "str",
                    "required": False,
                    "default": "min",
                    "description": "Idempotent operation: min or max",
                },
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="matrix",
            time_complexity="Preprocess O(n log n), query O(1)",
            space_complexity="O(n log n)",
            use_cases=[
                "Range minimum queries",
                "Range maximum queries",
                "Static array preprocessing",
                "Lowest common ancestor Euler-tour RMQ",
                "Fast interval analytics",
            ],
            pseudocode=(
                "st[0][i] = A[i]\n"
                "for k from 1 to floor(log2(n)):\n"
                "    span = 2^k\n"
                "    st[k][i] = op(st[k-1][i], st[k-1][i + span/2])\n"
                "\n"
                "query(l, r):\n"
                "    k = floor(log2(r-l+1))\n"
                "    return op(st[k][l], st[k][r - 2^k + 1])"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            values = _parse_values(str(params.get("values", "")))
        except ValueError:
            return
        if not values:
            return

        operation = str(params.get("operation", "min") or "min").strip().lower()
        if operation not in {"min", "max"}:
            operation = "min"
        combine = min if operation == "min" else max

        def clamp_index(raw: object, default: int) -> int:
            try:
                return int(str(raw).strip())
            except ValueError:
                return default

        n = len(values)
        query_left = max(0, min(n - 1, clamp_index(params.get("query_left", 0), 0)))
        query_right = max(0, min(n - 1, clamp_index(params.get("query_right", n - 1), n - 1)))
        if query_left > query_right:
            query_left, query_right = query_right, query_left

        max_level = int(log2(n)) + 1
        sparse_table: list[list[int | None]] = [[None for _ in range(n)] for _ in range(max_level)]
        log_table = [0] * (n + 1)
        for idx in range(2, n + 1):
            log_table[idx] = log_table[idx // 2] + 1

        rows = [f"2^{level}" for level in range(max_level)]
        columns = [str(index) for index in range(n)]

        def matrix_payload(highlights: list[dict] | None = None) -> dict:
            return {
                "title": f"Sparse Table ({operation})",
                "rows": rows,
                "columns": columns,
                "values": [["" if value is None else value for value in row] for row in sparse_table],
                "highlights": highlights or [],
            }

        def state(extra: dict | None = None) -> dict:
            payload = {
                "values": list(values),
                "operation": operation,
                "query_range": [query_left, query_right],
                "sparse_table": [["" if value is None else value for value in row] for row in sparse_table],
                "log_table": log_table[1:],
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.RENDER_MATRIX,
            target_type="matrix",
            target_id="sparse_table",
            value=matrix_payload(),
            message=f"Initialize sparse table for {n} values using {operation}",
            phase="init",
            state=state(),
        )

        for index, value in enumerate(values):
            sparse_table[0][index] = value
            yield Step(
                action=StepAction.UPDATE_MATRIX_CELL,
                target_type="matrix",
                target_id="sparse_table",
                value={"row": 0, "col": index, "value": value, "state": "updated"},
                message=f"Base interval [{index}, {index}] = {value}",
                phase="init",
                state=state({"level": 0, "interval": [index, index], "value": value}),
            )

        build_trace: list[dict] = []
        for level in range(1, max_level):
            span = 1 << level
            half = span >> 1
            for start in range(0, n - span + 1):
                left_value = sparse_table[level - 1][start]
                right_value = sparse_table[level - 1][start + half]
                if left_value is None or right_value is None:
                    continue
                value = combine(left_value, right_value)
                sparse_table[level][start] = value
                row = {
                    "level": level,
                    "start": start,
                    "interval": [start, start + span - 1],
                    "left_interval": [start, start + half - 1],
                    "right_interval": [start + half, start + span - 1],
                    "left_value": left_value,
                    "right_value": right_value,
                    "value": value,
                }
                build_trace.append(row)
                yield Step(
                    action=StepAction.UPDATE_MATRIX_CELL,
                    target_type="matrix",
                    target_id="sparse_table",
                    value={"row": level, "col": start, "value": value, "state": "updated"},
                    message=(
                        f"st[{level}][{start}] = {operation}({left_value}, {right_value}) = {value} "
                        f"for [{start}, {start + span - 1}]"
                    ),
                    phase="relax",
                    state=state({"build_trace": list(build_trace), "current_build": row}),
                )

        length = query_right - query_left + 1
        query_level = log_table[length]
        block_size = 1 << query_level
        left_block = {"level": query_level, "start": query_left, "end": query_left + block_size - 1}
        right_start = query_right - block_size + 1
        right_block = {"level": query_level, "start": right_start, "end": query_right}
        left_value = sparse_table[query_level][query_left]
        right_value = sparse_table[query_level][right_start]
        if left_value is None or right_value is None:
            return
        query_result = combine(left_value, right_value)
        query_blocks = [
            {**left_block, "value": left_value},
            {**right_block, "value": right_value},
        ]

        yield Step(
            action=StepAction.HIGHLIGHT_MATRIX_CELL,
            target_type="matrix",
            target_id="sparse_table",
            value={
                "cells": [
                    {"row": query_level, "col": query_left, "state": "path"},
                    {"row": query_level, "col": right_start, "state": "path"},
                ],
                "state": "path",
            },
            message=(
                f"Query [{query_left}, {query_right}] uses two 2^{query_level} blocks: "
                f"{left_value} and {right_value}"
            ),
            phase="explore",
            state=state({
                "build_trace": build_trace,
                "query_length": length,
                "query_level": query_level,
                "query_blocks": query_blocks,
            }),
        )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="matrix",
            target_id="sparse_table",
            message=f"Range {operation} for [{query_left}, {query_right}] = {query_result}",
            phase="result",
            state=state({
                "build_trace": build_trace,
                "query_length": length,
                "query_level": query_level,
                "query_blocks": query_blocks,
                "query_result": query_result,
            }),
        )

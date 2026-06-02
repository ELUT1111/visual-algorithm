"""Fibonacci dynamic programming visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class FibonacciDPAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="fibonacci_dp",
            category="dp",
            description="Compute Fibonacci numbers with bottom-up dynamic programming",
            emoji="🌀",
            parameters=[
                {"name": "n", "type": "int", "required": True, "description": "Index of Fibonacci number"}
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(n)",
            space_complexity="O(n)",
            use_cases=[
                "Introductory DP example",
                "Recurrence relation teaching",
                "Memoization vs tabulation",
                "Sequence generation",
            ],
            pseudocode=(
                "function Fibonacci(n):\n"
                "    dp[0] = 0; dp[1] = 1\n"
                "    for i from 2 to n:\n"
                "        dp[i] = dp[i-1] + dp[i-2]\n"
                "    return dp[n]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            n = int(params.get("n", 0))
        except ValueError:
            return
        if n < 0:
            return

        dp = [0] * (max(n, 1) + 1)
        if n >= 1:
            dp[1] = 1

        def items() -> list[dict]:
            return [{"value": idx, "meta": f"F={dp[idx]}"} for idx in range(n + 1)]

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="fib",
            value={"title": f"Fibonacci DP F({n})", "items": items()},
            message=f"Build Fibonacci table up to n={n}",
            phase="init",
            state={"n": n, "sequence": list(dp[: n + 1])},
        )

        if n == 0:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="array",
                target_id="fib",
                message="Fibonacci complete",
                phase="result",
                state={"n": 0, "fib_n": 0, "sequence": [0]},
            )
            return

        yield Step(
            action=StepAction.UPDATE_ARRAY_ITEM,
            target_type="array",
            target_id="fib",
            value={"index": 0, "value": 0, "state": "sorted", "meta": "F=0"},
            message="Base case F(0) = 0",
            phase="init",
            state={"n": n, "index": 0, "sequence": list(dp[: n + 1])},
        )
        yield Step(
            action=StepAction.UPDATE_ARRAY_ITEM,
            target_type="array",
            target_id="fib",
            value={"index": 1, "value": 1, "state": "sorted", "meta": "F=1"},
            message="Base case F(1) = 1",
            phase="init",
            state={"n": n, "index": 1, "sequence": list(dp[: n + 1])},
        )

        for i in range(2, n + 1):
            dp[i] = dp[i - 1] + dp[i - 2]
            yield Step(
                action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                target_type="array",
                target_id="fib",
                value={"indices": [i - 1, i - 2], "state": "compare"},
                message=f"F({i}) = F({i - 1}) + F({i - 2}) = {dp[i]}",
                phase="explore",
                state={"n": n, "index": i, "previous": [dp[i - 1], dp[i - 2]], "value": dp[i]},
            )
            yield Step(
                action=StepAction.UPDATE_ARRAY_ITEM,
                target_type="array",
                target_id="fib",
                value={"index": i, "value": dp[i], "state": "updated", "meta": f"F={dp[i]}"},
                message=f"Store F({i}) = {dp[i]}",
                phase="relax",
                state={"n": n, "index": i, "sequence": list(dp[: n + 1])},
            )

        yield Step(
            action=StepAction.HIGHLIGHT_ARRAY_ITEM,
            target_type="array",
            target_id="fib",
            value={"indices": [n], "state": "sorted"},
            message=f"Fibonacci complete. F({n}) = {dp[n]}",
            phase="result",
            state={"n": n, "fib_n": dp[n], "sequence": list(dp[: n + 1])},
        )

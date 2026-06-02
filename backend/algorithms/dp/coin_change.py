"""Coin change minimum coins dynamic programming visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_coins(coins_str: str) -> list[int]:
    return sorted({int(v.strip()) for v in coins_str.split(",") if v.strip()})


def _dp_table(dp: list[int], prev_coin: list[int | None], inf: int) -> list[dict]:
    rows = []
    for amount, value in enumerate(dp):
        rows.append(
            {
                "amount": amount,
                "min_coins": "∞" if value == inf else value,
                "previous_coin": prev_coin[amount],
                "reachable": value != inf,
            }
        )
    return rows


@registry.register
class CoinChangeAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="coin_change",
            category="dp",
            description="Find the minimum number of coins needed to make an amount",
            emoji="🪙",
            parameters=[
                {"name": "coins", "type": "str", "required": True, "description": "Comma-separated coin denominations"},
                {"name": "amount", "type": "int", "required": True, "description": "Target amount"},
            ],
            requires_graph=False,
            builds_structure=True,
            visualization="array",
            time_complexity="O(amount * coins)",
            space_complexity="O(amount)",
            use_cases=[
                "Change-making systems",
                "Budget decomposition",
                "Unbounded knapsack variants",
                "Dynamic programming teaching",
            ],
            pseudocode=(
                "function CoinChange(coins, amount):\n"
                "    dp[0] = 0; dp[1..amount] = infinity\n"
                "    for a from 1 to amount:\n"
                "        for coin in coins:\n"
                "            if coin <= a:\n"
                "                dp[a] = min(dp[a], dp[a - coin] + 1)\n"
                "    return dp[amount]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        try:
            coins = _parse_coins(str(params.get("coins", "")))
            amount = int(params.get("amount", 0))
        except ValueError:
            return
        if not coins or amount < 0:
            return

        inf = amount + 1
        dp = [inf for _ in range(amount + 1)]
        prev_coin: list[int | None] = [None for _ in range(amount + 1)]
        dp[0] = 0

        def display(value: int) -> str | int:
            return "∞" if value == inf else value

        def items() -> list[dict]:
            return [{"value": idx, "meta": f"dp={display(dp[idx])}"} for idx in range(amount + 1)]

        yield Step(
            action=StepAction.RENDER_ARRAY,
            target_type="array",
            target_id="main",
            value={"title": "Coin Change DP", "items": items()},
            message=f"Compute min coins for amount {amount} using {coins}",
            phase="init",
            state={
                "coins": coins,
                "amount": amount,
                "dp": [display(v) for v in dp],
                "dp_table": _dp_table(dp, prev_coin, inf),
            },
        )

        for current_amount in range(1, amount + 1):
            for coin in coins:
                if coin > current_amount:
                    continue

                candidate = dp[current_amount - coin] + 1
                previous_best = dp[current_amount]
                yield Step(
                    action=StepAction.HIGHLIGHT_ARRAY_ITEM,
                    target_type="array",
                    target_id="main",
                    value={"indices": [current_amount, current_amount - coin], "state": "compare"},
                    message=f"Try coin {coin}: dp[{current_amount - coin}] + 1 = {display(candidate)}",
                    phase="explore",
                    state={
                        "amount": current_amount,
                        "coin": coin,
                        "candidate": display(candidate),
                        "current_best": display(previous_best),
                        "transition": {
                            "from_amount": current_amount - coin,
                            "to_amount": current_amount,
                            "coin": coin,
                            "from_min_coins": display(dp[current_amount - coin]),
                            "candidate": display(candidate),
                            "previous_best": display(previous_best),
                            "improves": candidate < previous_best,
                        },
                        "dp": [display(v) for v in dp],
                        "dp_table": _dp_table(dp, prev_coin, inf),
                    },
                )

                if candidate < dp[current_amount]:
                    dp[current_amount] = candidate
                    prev_coin[current_amount] = coin
                    yield Step(
                        action=StepAction.UPDATE_ARRAY_ITEM,
                        target_type="array",
                        target_id="main",
                        value={"index": current_amount, "value": current_amount, "state": "swapped", "meta": f"dp={dp[current_amount]}"},
                        message=f"Update dp[{current_amount}] to {dp[current_amount]} using coin {coin}",
                        phase="relax",
                        state={
                            "amount": current_amount,
                            "coin": coin,
                            "dp": [display(v) for v in dp],
                            "dp_table": _dp_table(dp, prev_coin, inf),
                            "previous_coin": {idx: c for idx, c in enumerate(prev_coin) if c is not None},
                            "chosen_transition": {
                                "amount": current_amount,
                                "coin": coin,
                                "min_coins": dp[current_amount],
                            },
                        },
                    )

        combination: list[int] = []
        combination_steps: list[dict] = []
        cursor = amount
        while cursor > 0 and prev_coin[cursor] is not None:
            coin = prev_coin[cursor]
            combination.append(coin)
            combination_steps.append(
                {"amount": cursor, "coin": coin, "next_amount": cursor - coin}
            )
            cursor -= coin

        possible = dp[amount] != inf
        yield Step(
            action=StepAction.HIGHLIGHT_ARRAY_ITEM,
            target_type="array",
            target_id="main",
            value={"indices": [amount], "state": "sorted" if possible else "skipped"},
            message=(
                f"Minimum coins for {amount}: {dp[amount]} using {combination}"
                if possible
                else f"Amount {amount} cannot be formed by coins {coins}"
            ),
            phase="result",
            state={
                "possible": possible,
                "amount": amount,
                "min_coins": None if not possible else dp[amount],
                "combination": combination,
                "combination_steps": combination_steps,
                "dp": [display(v) for v in dp],
                "dp_table": _dp_table(dp, prev_coin, inf),
            },
        )

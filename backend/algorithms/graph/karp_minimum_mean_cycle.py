"""Karp's minimum mean cycle algorithm."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class KarpMinimumMeanCycleAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="karp_minimum_mean_cycle",
            category="graph",
            description="Find a directed cycle with minimum average edge weight using Karp's dynamic programming algorithm",
            emoji="MMC",
            parameters=[],
            requires_weighted=True,
            requires_directed=True,
            time_complexity="O(V * E)",
            space_complexity="O(V^2)",
            use_cases=[
                "Cycle-time bottleneck analysis",
                "Periodic scheduling optimization",
                "Arbitrage and negative-cycle screening",
                "Performance analysis of weighted state graphs",
            ],
            pseudocode=(
                "dp[0][v] = 0 for every vertex v\n"
                "for k from 1 to n:\n"
                "    dp[k][v] = min over incoming edges u->v of dp[k-1][u] + w(u,v)\n"
                "for each vertex v:\n"
                "    score[v] = max over k<n of (dp[n][v] - dp[k][v]) / (n-k)\n"
                "minimum mean cycle value = min score[v]\n"
                "recover a repeated vertex from the predecessor chain"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        n = len(node_ids)
        incoming: dict[str, list[tuple[str, float, str]]] = {node_id: [] for node_id in node_ids}
        edge_lookup: dict[tuple[str, str], str] = {}
        weight_lookup: dict[tuple[str, str], float] = {}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            weight = float(edge.weight)
            incoming.setdefault(edge.target, []).append((edge.source, weight, edge_id))
            edge_lookup[(edge.source, edge.target)] = edge_id
            weight_lookup[(edge.source, edge.target)] = weight

        def display(value: float):
            if value == float("inf"):
                return "Infinity"
            if value == float("-inf"):
                return "-Infinity"
            return int(value) if value == int(value) else round(value, 3)

        dp: list[dict[str, float]] = [{node_id: 0.0 for node_id in node_ids}]
        predecessor: list[dict[str, str | None]] = [{node_id: None for node_id in node_ids}]
        relaxation_trace: list[dict] = []

        def dp_table() -> dict:
            return {
                "type": "matrix",
                "rows": [str(i) for i in range(len(dp))],
                "columns": node_ids,
                "values": [[display(dp[row].get(node_id, float("inf"))) for node_id in node_ids] for row in range(len(dp))],
            }

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Start Karp minimum mean cycle DP",
            phase="init",
            state={"dp_table": dp_table(), "relaxation_trace": relaxation_trace},
        )

        for edge_count in range(1, n + 1):
            row = {node_id: float("inf") for node_id in node_ids}
            pred_row: dict[str, str | None] = {node_id: None for node_id in node_ids}

            for target in node_ids:
                for source, weight, edge_id in incoming.get(target, []):
                    if source not in dp[edge_count - 1]:
                        continue
                    candidate = dp[edge_count - 1][source] + weight
                    if candidate < row[target]:
                        row[target] = candidate
                        pred_row[target] = source
                        relaxation_trace.append(
                            {
                                "edge_count": edge_count,
                                "edge": edge_id,
                                "source": source,
                                "target": target,
                                "distance": display(candidate),
                            }
                        )

            dp.append(row)
            predecessor.append(pred_row)
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Computed minimum walk costs with exactly {edge_count} edge(s)",
                phase="relax",
                state={"edge_count": edge_count, "dp_table": dp_table(), "relaxation_trace": relaxation_trace},
            )

        mean_candidates = []
        best_vertex = None
        best_mean = float("inf")
        for vertex in node_ids:
            if dp[n][vertex] == float("inf"):
                continue
            ratios = []
            worst_ratio = float("-inf")
            for edge_count in range(n):
                if dp[edge_count][vertex] == float("inf"):
                    continue
                ratio = (dp[n][vertex] - dp[edge_count][vertex]) / (n - edge_count)
                ratios.append({"edge_count": edge_count, "mean": display(ratio)})
                worst_ratio = max(worst_ratio, ratio)
            if worst_ratio != float("-inf"):
                mean_candidates.append({"vertex": vertex, "max_mean": display(worst_ratio), "ratios": ratios})
                if worst_ratio < best_mean:
                    best_mean = worst_ratio
                    best_vertex = vertex

        if best_vertex is None:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="No directed cycle found",
                phase="result",
                state={"dp_table": dp_table(), "mean_candidates": mean_candidates, "minimum_mean_cycle": []},
            )
            return

        chain = []
        cursor = best_vertex
        for edge_count in range(n, -1, -1):
            chain.append(cursor)
            cursor = predecessor[edge_count].get(cursor)
            if cursor is None:
                break
        chain.reverse()

        last_seen: dict[str, int] = {}
        cycle_nodes: list[str] = []
        for index, node_id in enumerate(chain):
            if node_id in last_seen:
                cycle_nodes = chain[last_seen[node_id]: index + 1]
                break
            last_seen[node_id] = index

        if len(cycle_nodes) < 2:
            cycle_nodes = [best_vertex]

        cycle_edges = []
        cycle_weight = 0.0
        for source, target in zip(cycle_nodes, cycle_nodes[1:]):
            cycle_edges.append(edge_lookup.get((source, target), f"{source}-{target}"))
            cycle_weight += weight_lookup.get((source, target), 0.0)

        cycle_mean = cycle_weight / max(1, len(cycle_edges))
        result_state = {
            "dp_table": dp_table(),
            "mean_candidates": mean_candidates,
            "best_vertex": best_vertex,
            "cycle_mean": display(cycle_mean),
            "minimum_mean_cycle": cycle_nodes,
            "minimum_mean_cycle_edges": cycle_edges,
            "predecessor_trace": chain,
            "relaxation_trace": relaxation_trace,
        }

        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": cycle_nodes, "edges": cycle_edges},
            message=f"Minimum mean cycle {' -> '.join(cycle_nodes)} has mean {display(cycle_mean)}",
            phase="result",
            state=result_state,
        )

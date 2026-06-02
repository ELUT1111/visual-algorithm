"""Floyd-Warshall all-pairs shortest paths."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class FloydWarshallAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="floyd_warshall",
            category="graph",
            description="All-pairs shortest paths with dynamic programming",
            emoji="🧮",
            parameters=[],
            requires_weighted=True,
            time_complexity="O(V^3)",
            space_complexity="O(V^2)",
            use_cases=[
                "All-pairs shortest paths",
                "Dense weighted graphs",
                "Transitive closure variants",
                "Graphs with negative edges but no negative cycles",
            ],
            pseudocode=(
                "function FloydWarshall(graph):\n"
                "    dist[i][j] = edge weight or infinity\n"
                "    dist[i][i] = 0\n"
                "    for k in vertices:\n"
                "        for i in vertices:\n"
                "            for j in vertices:\n"
                "                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        nodes = [node.id for node in graph.nodes]
        idx = {node_id: i for i, node_id in enumerate(nodes)}
        size = len(nodes)
        dist = [[float("inf")] * size for _ in range(size)]

        for i in range(size):
            dist[i][i] = 0

        for edge in graph.edges:
            i = idx[edge.source]
            j = idx[edge.target]
            dist[i][j] = min(dist[i][j], edge.weight)
            if not graph.directed:
                dist[j][i] = min(dist[j][i], edge.weight)

        def display_value(value: float) -> str | int | float:
            if value == float("inf"):
                return "Infinity"
            if value == int(value):
                return int(value)
            return round(value, 2)

        def matrix_state(k: str | None = None, pair: list[str] | None = None) -> dict:
            return {
                "k": k or "",
                "current_pair": pair or [],
                "distance_matrix": {
                    "type": "matrix",
                    "rows": nodes,
                    "columns": nodes,
                    "values": [[display_value(value) for value in row] for row in dist],
                },
            }

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Initialize distance matrix",
            phase="init",
            state=matrix_state(),
        )

        for k in range(size):
            via = nodes[k]
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=via,
                value="current",
                message=f"Use {via} as intermediate node",
                phase="explore",
                state=matrix_state(via),
            )

            for i in range(size):
                for j in range(size):
                    if dist[i][k] == float("inf") or dist[k][j] == float("inf"):
                        continue
                    new_dist = dist[i][k] + dist[k][j]
                    if new_dist < dist[i][j]:
                        old_dist = dist[i][j]
                        dist[i][j] = new_dist
                        yield Step(
                            action=StepAction.ADD_MESSAGE,
                            target_type="node",
                            target_id=nodes[j],
                            message=(
                                f"Update dist[{nodes[i]}][{nodes[j]}]: "
                                f"{display_value(old_dist)} -> {display_value(new_dist)} via {via}"
                            ),
                            phase="relax",
                            state=matrix_state(via, [nodes[i], nodes[j]]),
                        )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=via,
                value="visited",
                message=f"Finished intermediate node {via}",
                phase="finalize",
                state=matrix_state(via),
            )

        negative_cycle_nodes = [nodes[i] for i in range(size) if dist[i][i] < 0]
        if negative_cycle_nodes:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Negative cycle detected involving: {', '.join(negative_cycle_nodes)}",
                phase="result",
                state={**matrix_state(), "negative_cycle_nodes": negative_cycle_nodes},
            )
            return

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Floyd-Warshall complete",
            phase="result",
            state=matrix_state(),
        )

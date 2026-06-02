"""Johnson's all-pairs shortest path algorithm."""
from __future__ import annotations

import heapq
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _display(value: float) -> str | int | float:
    if value == float("inf"):
        return "Infinity"
    if value == int(value):
        return int(value)
    return round(value, 2)


@registry.register
class JohnsonAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="johnson",
            category="graph",
            description="All-pairs shortest paths using Bellman-Ford potentials and Dijkstra",
            emoji="🧭",
            parameters=[],
            requires_weighted=True,
            requires_directed=True,
            time_complexity="O(VE + V(E + V) log V)",
            space_complexity="O(V^2)",
            use_cases=[
                "Sparse all-pairs shortest paths",
                "Graphs with negative edges and no negative cycles",
                "Routing-table precomputation",
                "Reweighting technique education",
            ],
            pseudocode=(
                "function Johnson(graph):\n"
                "    add super-source q with zero edges to every vertex\n"
                "    h = BellmanFord(graph, q)\n"
                "    reweight each edge w'(u,v)=w(u,v)+h[u]-h[v]\n"
                "    for each vertex s:\n"
                "        run Dijkstra with w' from s\n"
                "        convert distances back with h[v]-h[s]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        nodes = [node.id for node in graph.nodes]
        if not nodes:
            return

        edges = [(edge.source, edge.target, edge.weight, edge.id or f"{edge.source}-{edge.target}") for edge in graph.edges]
        h = {node: 0.0 for node in nodes}

        def matrix_state(matrix: dict[str, dict[str, float]] | None = None, source: str | None = None) -> dict:
            matrix = matrix or {row: {col: float("inf") for col in nodes} for row in nodes}
            return {
                "source": source or "",
                "potentials": {node: _display(value) for node, value in h.items()},
                "distance_matrix": {
                    "type": "matrix",
                    "rows": nodes,
                    "columns": nodes,
                    "values": [[_display(matrix[row][col]) for col in nodes] for row in nodes],
                },
            }

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Add virtual source and compute Johnson potentials",
            phase="init",
            state=matrix_state(),
        )

        for iteration in range(len(nodes)):
            updated = False
            for u, v, weight, edge_id in edges:
                if h[u] + weight < h[v]:
                    h[v] = h[u] + weight
                    updated = True
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        value="exploring",
                        message=f"Potential update h[{v}] = {_display(h[v])}",
                        phase="relax",
                        state={**matrix_state(), "iteration": iteration + 1, "edge": edge_id},
                    )
            if not updated:
                break
        else:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="Negative cycle detected; Johnson cannot continue",
                phase="result",
                state={**matrix_state(), "negative_cycle": True},
            )
            return

        reweighted_adj: dict[str, list[tuple[str, float, str]]] = {node: [] for node in nodes}
        for u, v, weight, edge_id in edges:
            reweighted = weight + h[u] - h[v]
            reweighted_adj.setdefault(u, []).append((v, reweighted, edge_id))

        all_pairs = {row: {col: float("inf") for col in nodes} for row in nodes}

        for source in nodes:
            dist = {node: float("inf") for node in nodes}
            dist[source] = 0
            heap = [(0.0, source)]

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=source,
                value="current",
                message=f"Run Dijkstra from {source} on reweighted graph",
                phase="explore",
                state={**matrix_state(all_pairs, source), "queue": [[0, source]]},
            )

            while heap:
                current_dist, current = heapq.heappop(heap)
                if current_dist != dist[current]:
                    continue
                for neighbor, weight, edge_id in reweighted_adj.get(current, []):
                    candidate = current_dist + weight
                    if candidate < dist[neighbor]:
                        dist[neighbor] = candidate
                        heapq.heappush(heap, (candidate, neighbor))
                        yield Step(
                            action=StepAction.HIGHLIGHT_EDGE,
                            target_type="edge",
                            target_id=edge_id,
                            value="exploring",
                            message=f"Reweighted relax {current} -> {neighbor}: {_display(candidate)}",
                            phase="relax",
                            state={
                                **matrix_state(all_pairs, source),
                                "current": current,
                                "neighbor": neighbor,
                                "reweighted_distance": _display(candidate),
                            },
                        )

            for target in nodes:
                if dist[target] != float("inf"):
                    all_pairs[source][target] = dist[target] - h[source] + h[target]

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id=source,
                message=f"Finished shortest paths from {source}",
                phase="finalize",
                state=matrix_state(all_pairs, source),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Johnson all-pairs shortest paths complete",
            phase="result",
            state={**matrix_state(all_pairs), "negative_cycle": False},
        )

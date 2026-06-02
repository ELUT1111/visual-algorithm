"""Bellman-Ford shortest path algorithm."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BellmanFordAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="bellman_ford",
            category="graph",
            description="Shortest path with negative weight support",
            emoji="⚡",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"}
            ],
            requires_weighted=True,
            time_complexity="O(V * E)",
            space_complexity="O(V)",
            use_cases=[
                "Graphs with negative edge weights",
                "Detecting negative cycles",
                "Currency arbitrage detection",
                "Network flow with costs",
            ],
            pseudocode=(
                "function BellmanFord(graph, source):\n"
                "    dist[source] = 0\n"
                "    for each vertex v != source: dist[v] = infinity\n"
                "    repeat (V - 1) times:\n"
                "        for each edge (u, v, w) in graph:\n"
                "            if dist[u] + w < dist[v]:\n"
                "                dist[v] = dist[u] + w\n"
                "                prev[v] = u\n"
                "    // Check for negative cycles\n"
                "    for each edge (u, v, w) in graph:\n"
                "        if dist[u] + w < dist[v]:\n"
                "            report \"Negative cycle detected\"\n"
                "    return dist, prev"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source")
        if not source:
            source = graph.nodes[0].id if graph.nodes else None
        if not source:
            return

        node_ids = [n.id for n in graph.nodes]
        distances = {nid: float("inf") for nid in node_ids}
        distances[source] = 0
        prev = {nid: None for nid in node_ids}

        def format_distances() -> dict[str, str | float]:
            return {
                node_id: ("∞" if dist == float("inf") else dist)
                for node_id, dist in distances.items()
            }

        def algorithm_state(iteration: int | None = None, edge: str | None = None, direction: str | None = None) -> dict:
            return {
                "source": source,
                "iteration": iteration,
                "edge": edge,
                "direction": direction,
                "distances": format_distances(),
                "previous": {node: pred for node, pred in prev.items() if pred is not None},
            }

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Starting Bellman-Ford from {source}",
            phase="init",
            state=algorithm_state(),
        )

        for nid in node_ids:
            if nid != source:
                yield Step(
                    action=StepAction.UPDATE_NODE_LABEL,
                    target_type="node",
                    target_id=nid,
                    value=f"{nid}\n∞",
                    message=f"Distance to {nid}: ∞",
                    phase="init",
                    state=algorithm_state(),
                )
            else:
                yield Step(
                    action=StepAction.UPDATE_NODE_LABEL,
                    target_type="node",
                    target_id=nid,
                    value=f"{nid}\n0",
                    message=f"Distance to {nid}: 0",
                    phase="init",
                    state=algorithm_state(),
                )

        num_nodes = len(node_ids)

        for i in range(num_nodes - 1):
            updated = False

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"--- Iteration {i + 1}/{num_nodes - 1} ---",
                phase="explore",
                state=algorithm_state(i + 1),
            )

            for edge in graph.edges:
                u, v, w = edge.source, edge.target, edge.weight
                edge_id = edge.id or f"{u}-{v}"

                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Checking {u} → {v} (weight={w})",
                    phase="relax",
                    state=algorithm_state(i + 1, edge_id, "forward"),
                )

                if distances[u] != float("inf") and distances[u] + w < distances[v]:
                    old = distances[v]
                    distances[v] = distances[u] + w
                    prev[v] = u
                    updated = True

                    yield Step(
                        action=StepAction.UPDATE_NODE_LABEL,
                        target_type="node",
                        target_id=v,
                        value=f"{v}\n{distances[v]}",
                        message=f"Relaxed {v}: {old} → {distances[v]}",
                        phase="relax",
                        state=algorithm_state(i + 1, edge_id, "forward"),
                    )

                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=v,
                        value="exploring",
                        message="",
                        phase="relax",
                        state=algorithm_state(i + 1, edge_id, "forward"),
                    )

                # Check reverse edge for undirected graphs
                if not graph.directed:
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        value="exploring",
                        message=f"Checking {v} → {u} (weight={w})",
                        phase="relax",
                        state=algorithm_state(i + 1, edge_id, "reverse"),
                    )

                    if distances[v] != float("inf") and distances[v] + w < distances[u]:
                        old = distances[u]
                        distances[u] = distances[v] + w
                        prev[u] = v
                        updated = True

                        yield Step(
                            action=StepAction.UPDATE_NODE_LABEL,
                            target_type="node",
                            target_id=u,
                            value=f"{u}\n{distances[u]}",
                            message=f"Relaxed {u}: {old} → {distances[u]}",
                            phase="relax",
                            state=algorithm_state(i + 1, edge_id, "reverse"),
                        )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                    state=algorithm_state(i + 1, edge_id),
                )

            if not updated:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id="",
                    message="No updates in this iteration - early termination",
                    phase="finalize",
                    state=algorithm_state(i + 1),
                )
                break

        # Check for negative cycles
        has_negative_cycle = False
        for edge in graph.edges:
            u, v, w = edge.source, edge.target, edge.weight
            edge_id_fwd = edge.id or f"{u}-{v}"
            edge_id_rev = f"{v}-{u}"

            if distances[u] != float("inf") and distances[u] + w < distances[v]:
                has_negative_cycle = True
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id_fwd,
                    value="path",
                    message=f"Negative cycle detected via edge {u} → {v}!",
                    phase="result",
                    state=algorithm_state(num_nodes - 1, edge_id_fwd, "forward"),
                )
                break

            if not graph.directed and distances[v] != float("inf") and distances[v] + w < distances[u]:
                has_negative_cycle = True
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id_rev,
                    value="path",
                    message=f"Negative cycle detected via edge {v} → {u}!",
                    phase="result",
                    state=algorithm_state(num_nodes - 1, edge_id_rev, "reverse"),
                )
                break

        if not has_negative_cycle:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="No negative cycles detected. Bellman-Ford complete.",
                phase="result",
                state=algorithm_state(num_nodes - 1),
            )
            # Mark settled nodes
            for nid in node_ids:
                if nid != source and distances[nid] < float("inf"):
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=nid,
                        value="visited",
                        message=f"Final distance to {nid}: {distances[nid]}",
                        phase="result",
                        state=algorithm_state(num_nodes - 1),
                    )

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

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Starting Bellman-Ford from {source}",
            phase="init",
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
                )
            else:
                yield Step(
                    action=StepAction.UPDATE_NODE_LABEL,
                    target_type="node",
                    target_id=nid,
                    value=f"{nid}\n0",
                    message=f"Distance to {nid}: 0",
                    phase="init",
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
                    )

                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=v,
                        value="exploring",
                        message="",
                        phase="relax",
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
                        )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                )

            if not updated:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id="",
                    message="No updates in this iteration - early termination",
                    phase="finalize",
                )
                break

        # Check for negative cycles
        has_negative_cycle = False
        for edge in graph.edges:
            u, v, w = edge.source, edge.target, edge.weight
            if distances[u] != float("inf") and distances[u] + w < distances[v]:
                has_negative_cycle = True
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge.id or f"{u}-{v}",
                    value="path",
                    message=f"Negative cycle detected via edge {u} → {v}!",
                    phase="result",
                )
                break

        if not has_negative_cycle:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="No negative cycles detected. Bellman-Ford complete.",
                phase="result",
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
                    )

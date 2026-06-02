"""SPFA shortest paths with queue-based relaxation."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _display(value: float) -> str | int | float:
    if value == float("inf"):
        return "∞"
    if value == int(value):
        return int(value)
    return round(value, 2)


@registry.register
class SPFAAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="spfa",
            category="graph",
            description="Queue-optimized Bellman-Ford shortest paths",
            emoji="🚦",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"}
            ],
            requires_weighted=True,
            time_complexity="O(E) average, O(VE) worst",
            space_complexity="O(V)",
            use_cases=[
                "Shortest paths with negative edges",
                "Sparse graph relaxation",
                "Queue-based Bellman-Ford teaching",
                "Negative cycle detection",
            ],
            pseudocode=(
                "function SPFA(graph, source):\n"
                "    dist[source] = 0; push source into queue\n"
                "    while queue is not empty:\n"
                "        u = pop queue\n"
                "        for each edge u -> v:\n"
                "            if dist[u] + w < dist[v]:\n"
                "                dist[v] = dist[u] + w\n"
                "                if v not in queue: push v\n"
                "                if v is relaxed too often: report negative cycle"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source") or (graph.nodes[0].id if graph.nodes else None)
        if not source:
            return

        node_ids = [node.id for node in graph.nodes]
        adj: dict[str, list[tuple[str, float, str]]] = {node_id: [] for node_id in node_ids}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adj.setdefault(edge.source, []).append((edge.target, edge.weight, edge_id))
            if not graph.directed:
                adj.setdefault(edge.target, []).append((edge.source, edge.weight, edge_id))

        distances = {node_id: float("inf") for node_id in node_ids}
        previous: dict[str, str | None] = {node_id: None for node_id in node_ids}
        in_queue: set[str] = {source}
        relax_count = {node_id: 0 for node_id in node_ids}
        queue: deque[str] = deque([source])
        distances[source] = 0

        def state(current: str | None = None, edge_id: str | None = None) -> dict:
            return {
                "source": source,
                "current": current,
                "edge": edge_id,
                "queue": list(queue),
                "in_queue": sorted(in_queue),
                "relax_count": dict(relax_count),
                "distances": {node: _display(dist) for node, dist in distances.items()},
                "previous": {node: pred for node, pred in previous.items() if pred is not None},
            }

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Start SPFA from {source}",
            phase="init",
            state=state(source),
        )

        while queue:
            current = queue.popleft()
            in_queue.discard(current)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Pop {current} from queue",
                phase="explore",
                state=state(current),
            )

            for neighbor, weight, edge_id in adj.get(current, []):
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Relax edge {current} -> {neighbor} (weight={weight})",
                    phase="relax",
                    state=state(current, edge_id),
                )

                candidate = distances[current] + weight
                if distances[current] != float("inf") and candidate < distances[neighbor]:
                    old = distances[neighbor]
                    distances[neighbor] = candidate
                    previous[neighbor] = current
                    relax_count[neighbor] += 1

                    yield Step(
                        action=StepAction.UPDATE_NODE_LABEL,
                        target_type="node",
                        target_id=neighbor,
                        value=f"{neighbor}\n{_display(candidate)}",
                        message=f"Update {neighbor}: {_display(old)} -> {_display(candidate)}",
                        phase="relax",
                        state=state(current, edge_id),
                    )

                    if relax_count[neighbor] >= len(node_ids):
                        yield Step(
                            action=StepAction.HIGHLIGHT_EDGE,
                            target_type="edge",
                            target_id=edge_id,
                            value="path",
                            message=f"Negative cycle detected while relaxing {neighbor}",
                            phase="result",
                            state={**state(current, edge_id), "negative_cycle": True},
                        )
                        return

                    if neighbor not in in_queue:
                        queue.append(neighbor)
                        in_queue.add(neighbor)
                        yield Step(
                            action=StepAction.SET_NODE_COLOR,
                            target_type="node",
                            target_id=neighbor,
                            value="exploring",
                            message=f"Push {neighbor} into queue",
                            phase="relax",
                            state=state(current, edge_id),
                        )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                    state=state(current),
                )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="visited",
                message=f"Finished outgoing edges from {current}",
                phase="finalize",
                state=state(current),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="SPFA complete",
            phase="result",
            state={**state(), "negative_cycle": False},
        )

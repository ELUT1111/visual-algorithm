"""Dijkstra's shortest path algorithm."""
from __future__ import annotations

import heapq
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class DijkstraAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="dijkstra",
            category="graph",
            description="Find shortest path from source to all nodes",
            emoji="🛤️",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"}
            ],
            requires_weighted=True,
            allows_negative_weights=False,
            time_complexity="O((V + E) log V)",
            space_complexity="O(V)",
            use_cases=[
                "GPS navigation and mapping",
                "Network routing protocols (OSPF)",
                "Social network shortest connection",
                "Game pathfinding on weighted grids",
            ],
            pseudocode=(
                "function Dijkstra(graph, source):\n"
                "    dist[source] = 0\n"
                "    for each vertex v != source: dist[v] = infinity\n"
                "    Q = priority queue with all vertices\n"
                "    while Q is not empty:\n"
                "        u = vertex in Q with min dist[u]\n"
                "        remove u from Q\n"
                "        for each neighbor v of u:\n"
                "            alt = dist[u] + weight(u, v)\n"
                "            if alt < dist[v]:\n"
                "                dist[v] = alt\n"
                "                prev[v] = u\n"
                "    return dist, prev"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source")
        if not source:
            source = graph.nodes[0].id if graph.nodes else None
        if not source:
            return

        # Build adjacency list
        adj: dict[str, list[tuple[str, float, str]]] = {n.id: [] for n in graph.nodes}
        for e in graph.edges:
            adj.setdefault(e.source, []).append((e.target, e.weight, e.id))
            if not graph.directed:
                adj.setdefault(e.target, []).append((e.source, e.weight, e.id))

        distances = {n.id: float("inf") for n in graph.nodes}
        distances[source] = 0
        prev = {n.id: None for n in graph.nodes}
        visited = set()
        heap = [(0, source)]

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Starting Dijkstra from node {source}",
            phase="init",
        )

        for node in graph.nodes:
            if node.id != source:
                yield Step(
                    action=StepAction.UPDATE_NODE_LABEL,
                    target_type="node",
                    target_id=node.id,
                    value=f"{node.label}\n∞",
                    message=f"Distance to {node.id}: ∞",
                    phase="init",
                )

        yield Step(
            action=StepAction.UPDATE_NODE_LABEL,
            target_type="node",
            target_id=source,
            value=f"{source}\n0",
            message=f"Distance to {source}: 0",
            phase="init",
        )

        while heap:
            dist, current = heapq.heappop(heap)

            if current in visited:
                continue

            visited.add(current)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Visiting node {current} (distance = {dist})",
                phase="explore",
            )

            for neighbor, weight, edge_id in adj.get(current, []):
                if neighbor in visited:
                    continue

                new_dist = dist + weight

                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Checking edge {current} → {neighbor} (weight={weight})",
                    phase="relax",
                )

                if new_dist < distances[neighbor]:
                    old_dist = distances[neighbor]
                    distances[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(heap, (new_dist, neighbor))

                    yield Step(
                        action=StepAction.UPDATE_NODE_LABEL,
                        target_type="node",
                        target_id=neighbor,
                        value=f"{neighbor}\n{new_dist}",
                        message=f"Updated distance to {neighbor}: {old_dist} → {new_dist}",
                        phase="relax",
                    )

                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=neighbor,
                        value="exploring",
                        message=f"Node {neighbor} updated",
                        phase="relax",
                    )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="settled",
                message=f"Node {current} settled (final distance = {dist})",
                phase="finalize",
            )

        # Show shortest paths
        yield Step(
            action=StepAction.RESET_ALL,
            target_type="node",
            target_id="",
            message="All nodes settled. Showing results.",
            phase="result",
        )

        for node in graph.nodes:
            if node.id != source and distances[node.id] < float("inf"):
                # Trace path
                path = []
                current = node.id
                while current is not None:
                    path.append(current)
                    current = prev[current]
                path.reverse()

                yield Step(
                    action=StepAction.MARK_PATH,
                    target_type="node",
                    target_id="",
                    value=path,
                    message=f"Shortest path to {node.id}: {' → '.join(path)} (distance = {distances[node.id]})",
                    phase="result",
                )

                # Reset path highlight before next
                for pid in path:
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=pid,
                        value="default",
                        message="",
                        phase="result",
                    )

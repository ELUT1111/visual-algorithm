"""Longest path / critical path in a weighted DAG."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class DAGLongestPathAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="dag_longest_path",
            category="graph",
            description="Find longest weighted paths in a DAG and highlight the critical path",
            emoji="CP",
            parameters=[
                {"name": "source", "type": "str", "required": False, "default": "", "description": "Optional source node ID"},
                {"name": "target", "type": "str", "required": False, "default": "", "description": "Optional target node ID"},
            ],
            requires_weighted=True,
            requires_directed=True,
            requires_dag=True,
            time_complexity="O(V + E)",
            space_complexity="O(V + E)",
            use_cases=[
                "Critical path scheduling",
                "Build pipeline duration analysis",
                "Project planning on dependency DAGs",
                "Longest dependency chain detection",
            ],
            pseudocode=(
                "order = topological_sort(DAG)\n"
                "dist[source] = 0\n"
                "for u in order:\n"
                "    for each edge u -> v:\n"
                "        if dist[u] + weight(u,v) > dist[v]:\n"
                "            dist[v] = dist[u] + weight(u,v)\n"
                "            prev[v] = u\n"
                "critical_path = backtrack from target with best dist"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        source = str(params.get("source", "") or "").strip() or None
        target = str(params.get("target", "") or "").strip() or None

        adjacency: dict[str, list[tuple[str, str, float]]] = {node_id: [] for node_id in node_ids}
        indegree: dict[str, int] = {node_id: 0 for node_id in node_ids}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id, edge.weight))
            indegree[edge.target] = indegree.get(edge.target, 0) + 1

        queue = deque([node_id for node_id in node_ids if indegree.get(node_id, 0) == 0])
        topo_order: list[str] = []
        topo_indegree = dict(indegree)
        while queue:
            current = queue.popleft()
            topo_order.append(current)
            for neighbor, _, _ in adjacency.get(current, []):
                topo_indegree[neighbor] -= 1
                if topo_indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo_order) != len(node_ids):
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="Cannot compute DAG longest path: graph contains a cycle",
                phase="result",
                state={"topological_order": topo_order, "cycle_detected": True},
            )
            return

        if source not in node_ids:
            source = topo_order[0]

        distances = {node_id: float("-inf") for node_id in node_ids}
        previous: dict[str, str | None] = {node_id: None for node_id in node_ids}
        distances[source] = 0

        def display_distances() -> dict[str, str | int | float]:
            return {
                node_id: ("-Infinity" if value == float("-inf") else (int(value) if value == int(value) else value))
                for node_id, value in distances.items()
            }

        def state(extra: dict | None = None) -> dict:
            payload = {
                "source": source,
                "target": target,
                "topological_order": topo_order,
                "distances": display_distances(),
                "previous": {node: pred for node, pred in previous.items() if pred is not None},
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Topological order for longest path: {' -> '.join(topo_order)}",
            phase="init",
            state=state(),
        )

        for node_id in topo_order:
            label_value = display_distances()[node_id]
            yield Step(
                action=StepAction.UPDATE_NODE_LABEL,
                target_type="node",
                target_id=node_id,
                value=f"{node_id}\n{label_value}",
                message=f"Longest distance to {node_id}: {label_value}",
                phase="init",
                state=state({"current": node_id}),
            )

        for current in topo_order:
            if distances[current] == float("-inf"):
                continue

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Relax outgoing edges from {current}",
                phase="explore",
                state=state({"current": current}),
            )

            for neighbor, edge_id, weight in adjacency.get(current, []):
                candidate = distances[current] + weight
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Check {current} -> {neighbor}: {distances[current]:g} + {weight:g} = {candidate:g}",
                    phase="relax",
                    state=state({"edge": edge_id, "candidate": candidate}),
                )

                if candidate > distances[neighbor]:
                    distances[neighbor] = candidate
                    previous[neighbor] = current
                    yield Step(
                        action=StepAction.UPDATE_NODE_LABEL,
                        target_type="node",
                        target_id=neighbor,
                        value=f"{neighbor}\n{candidate:g}",
                        message=f"Update longest distance to {neighbor}: {candidate:g}",
                        phase="relax",
                        state=state({"updated": neighbor, "edge": edge_id}),
                    )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                    state=state({"edge": edge_id}),
                )

        if target not in node_ids:
            reachable = [node_id for node_id, value in distances.items() if value != float("-inf")]
            target = max(reachable, key=lambda node_id: distances[node_id]) if reachable else source

        critical_path: list[str] = []
        cursor = target
        while cursor is not None and cursor in node_ids:
            critical_path.append(cursor)
            if cursor == source:
                break
            cursor = previous.get(cursor)
        critical_path.reverse()

        path_edges: list[str] = []
        for start, end in zip(critical_path, critical_path[1:]):
            for neighbor, edge_id, _ in adjacency.get(start, []):
                if neighbor == end:
                    path_edges.append(edge_id)
                    break

        longest_distance = distances[target]
        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": critical_path, "edges": path_edges},
            message=f"Critical path {' -> '.join(critical_path)} has length {longest_distance:g}",
            phase="result",
            state=state({
                "target": target,
                "critical_path": critical_path,
                "critical_path_edges": path_edges,
                "longest_distance": int(longest_distance) if longest_distance == int(longest_distance) else longest_distance,
            }),
        )

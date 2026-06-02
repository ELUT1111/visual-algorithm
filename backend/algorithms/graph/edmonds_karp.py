"""Edmonds-Karp maximum flow visualization."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class EdmondsKarpAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="edmonds_karp",
            category="graph",
            description="Maximum flow using BFS augmenting paths",
            emoji="🌊",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"},
                {"name": "target", "type": "str", "required": True, "description": "Sink node ID"},
            ],
            requires_weighted=True,
            requires_directed=True,
            allows_negative_weights=False,
            time_complexity="O(VE^2)",
            space_complexity="O(E)",
            use_cases=[
                "Network throughput",
                "Bipartite matching foundations",
                "Traffic and logistics flow",
                "Residual network education",
            ],
            pseudocode=(
                "function EdmondsKarp(graph, source, sink):\n"
                "    flow = 0\n"
                "    while BFS finds an augmenting path:\n"
                "        bottleneck = minimum residual capacity on path\n"
                "        augment flow along that path\n"
                "        flow += bottleneck\n"
                "    return flow"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source")
        sink = params.get("target")
        if not source or not sink or source == sink:
            return

        capacities: dict[tuple[str, str], float] = {}
        edge_ids: dict[tuple[str, str], str] = {}
        for edge in graph.edges:
            if edge.weight <= 0:
                continue
            key = (edge.source, edge.target)
            capacities[key] = capacities.get(key, 0) + edge.weight
            edge_ids[key] = edge.id or f"{edge.source}-{edge.target}"

        flow = {key: 0.0 for key in capacities}
        max_flow = 0.0
        augmentations: list[dict] = []

        def display(value: float) -> int | float:
            return int(value) if value == int(value) else round(value, 2)

        def residual_edges(node: str) -> list[tuple[str, tuple[str, str], str, float]]:
            result = []
            for (u, v), cap in capacities.items():
                f = flow[(u, v)]
                if u == node and cap - f > 0:
                    result.append((v, (u, v), "forward", cap - f))
                if v == node and f > 0:
                    result.append((u, (u, v), "reverse", f))
            return result

        def flow_table() -> list[dict]:
            return [
                {
                    "edge": f"{u}->{v}",
                    "flow": flow[(u, v)],
                    "capacity": cap,
                    "residual": cap - flow[(u, v)],
                }
                for (u, v), cap in capacities.items()
            ]

        def residual_network() -> list[dict]:
            rows = []
            for (u, v), cap in capacities.items():
                f = flow[(u, v)]
                forward_residual = cap - f
                reverse_residual = f
                if forward_residual > 0:
                    rows.append(
                        {
                            "from": u,
                            "to": v,
                            "direction": "forward",
                            "residual": display(forward_residual),
                            "flow": display(f),
                            "capacity": display(cap),
                        }
                    )
                if reverse_residual > 0:
                    rows.append(
                        {
                            "from": v,
                            "to": u,
                            "direction": "reverse",
                            "residual": display(reverse_residual),
                            "flow": display(f),
                            "capacity": display(cap),
                        }
                    )
            return rows

        def path_edges(path, bottleneck: float) -> list[dict]:
            return [
                {
                    "from": start,
                    "to": end,
                    "edge": f"{key[0]}->{key[1]}",
                    "direction": direction,
                    "residual_before": display(residual),
                    "bottleneck": residual == bottleneck,
                }
                for start, end, key, direction, residual in path
            ]

        def bfs():
            parent: dict[str, tuple[str, tuple[str, str], str, float]] = {}
            queue = deque([source])
            seen = {source}
            bfs_layers = {source: 0}
            scanned_edges: list[dict] = []
            while queue:
                current = queue.popleft()
                for neighbor, key, direction, residual in residual_edges(current):
                    scanned_edges.append(
                        {
                            "from": current,
                            "to": neighbor,
                            "edge": f"{key[0]}->{key[1]}",
                            "direction": direction,
                            "residual": display(residual),
                        }
                    )
                    if neighbor in seen or residual <= 0:
                        continue
                    seen.add(neighbor)
                    bfs_layers[neighbor] = bfs_layers[current] + 1
                    parent[neighbor] = (current, key, direction, residual)
                    if neighbor == sink:
                        path = []
                        cursor = sink
                        bottleneck = float("inf")
                        while cursor != source:
                            prev, edge_key, edge_dir, edge_residual = parent[cursor]
                            path.append((prev, cursor, edge_key, edge_dir, edge_residual))
                            bottleneck = min(bottleneck, edge_residual)
                            cursor = prev
                        path.reverse()
                        return path, bottleneck, sorted(seen), bfs_layers, scanned_edges
                    queue.append(neighbor)
            return [], 0, sorted(seen), bfs_layers, scanned_edges

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Start Edmonds-Karp from {source} to {sink}",
            phase="init",
            state={
                "source": source,
                "sink": sink,
                "max_flow": max_flow,
                "flow_table": flow_table(),
                "residual_network": residual_network(),
            },
        )

        while True:
            path, bottleneck, seen, bfs_layers, scanned_edges = bfs()
            if not path:
                break

            path_nodes = [path[0][0]] + [step[1] for step in path]
            visual_path_edges = [edge_ids[key] for _, _, key, direction, _ in path if direction == "forward" and key in edge_ids]
            structured_path_edges = path_edges(path, bottleneck)

            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": path_nodes, "edges": visual_path_edges},
                message=f"Augmenting path {' -> '.join(path_nodes)} with bottleneck {bottleneck}",
                phase="explore",
                state={
                    "source": source,
                    "sink": sink,
                    "visited_by_bfs": seen,
                    "bfs_layers": bfs_layers,
                    "scanned_residual_edges": scanned_edges,
                    "augmenting_path": path_nodes,
                    "augmenting_path_edges": structured_path_edges,
                    "bottleneck": display(bottleneck),
                    "bottleneck_edges": [edge for edge in structured_path_edges if edge["bottleneck"]],
                    "max_flow": max_flow,
                    "flow_table": flow_table(),
                    "residual_network": residual_network(),
                },
            )

            for _, _, key, direction, _ in path:
                if direction == "forward":
                    flow[key] += bottleneck
                else:
                    flow[key] -= bottleneck

            max_flow += bottleneck
            augmentations.append(
                {
                    "path": path_nodes,
                    "edges": structured_path_edges,
                    "bottleneck": display(bottleneck),
                    "flow_after": display(max_flow),
                }
            )

            for key in capacities:
                edge_id = edge_ids[key]
                yield Step(
                    action=StepAction.UPDATE_EDGE_LABEL,
                    target_type="edge",
                    target_id=edge_id,
                    value=f"{flow[key]:g}/{capacities[key]:g}",
                    message=f"Flow on {key[0]} -> {key[1]} is {flow[key]:g}/{capacities[key]:g}",
                    phase="relax",
                    state={
                        "max_flow": display(max_flow),
                        "flow_table": flow_table(),
                        "residual_network": residual_network(),
                        "augmentations": list(augmentations),
                    },
                )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Edmonds-Karp complete. Max flow = {max_flow:g}",
            phase="result",
            state={
                "max_flow": display(max_flow),
                "flow_table": flow_table(),
                "residual_network": residual_network(),
                "augmentations": augmentations,
            },
        )

"""Dinic maximum flow visualization."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class DinicAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="dinic",
            category="graph",
            description="Maximum flow using level graphs and blocking flows",
            emoji="🏗️",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"},
                {"name": "target", "type": "str", "required": True, "description": "Sink node ID"},
            ],
            requires_weighted=True,
            requires_directed=True,
            allows_negative_weights=False,
            time_complexity="O(V^2E)",
            space_complexity="O(E)",
            use_cases=[
                "High-throughput max-flow problems",
                "Bipartite matching",
                "Cut/flow analysis",
                "Level graph education",
            ],
            pseudocode=(
                "function Dinic(graph, source, sink):\n"
                "    while BFS builds a level graph reaching sink:\n"
                "        reset current-edge pointers\n"
                "        while DFS sends flow through level graph:\n"
                "            add the blocking flow\n"
                "    return max_flow"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source")
        sink = params.get("target")
        if not source or not sink or source == sink:
            return

        node_ids = [node.id for node in graph.nodes]
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

        def residual_from(node: str) -> list[tuple[str, tuple[str, str], str, float]]:
            result = []
            for (u, v), cap in capacities.items():
                f = flow[(u, v)]
                if u == node and cap - f > 0:
                    result.append((v, (u, v), "forward", cap - f))
                if v == node and f > 0:
                    result.append((u, (u, v), "reverse", f))
            return result

        def build_levels() -> dict[str, int]:
            levels = {node: -1 for node in node_ids}
            levels[source] = 0
            queue = deque([source])
            while queue:
                current = queue.popleft()
                for neighbor, _, _, residual in residual_from(current):
                    if residual > 0 and levels.get(neighbor, -1) < 0:
                        levels[neighbor] = levels[current] + 1
                        queue.append(neighbor)
            return levels

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

        def level_graph_edges(levels: dict[str, int]) -> list[dict]:
            rows = []
            for node in node_ids:
                for neighbor, key, direction, residual in residual_from(node):
                    if levels.get(node, -1) >= 0 and levels.get(neighbor, -1) == levels[node] + 1:
                        rows.append(
                            {
                                "from": node,
                                "to": neighbor,
                                "edge": f"{key[0]}->{key[1]}",
                                "direction": direction,
                                "residual": display(residual),
                                "from_level": levels[node],
                                "to_level": levels[neighbor],
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

        def dfs_path(levels: dict[str, int]) -> tuple[list[tuple[str, str, tuple[str, str], str, float]], float]:
            stack = [(source, [], float("inf"), {source})]
            while stack:
                current, path, bottleneck, seen = stack.pop()
                if current == sink:
                    return path, bottleneck
                for neighbor, key, direction, residual in residual_from(current):
                    if neighbor in seen or residual <= 0:
                        continue
                    if levels.get(neighbor, -1) != levels.get(current, -1) + 1:
                        continue
                    stack.append((neighbor, path + [(current, neighbor, key, direction, residual)], min(bottleneck, residual), seen | {neighbor}))
            return [], 0

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Start Dinic from {source} to {sink}",
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
            levels = build_levels()
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Build level graph: sink level is {levels.get(sink, -1)}",
                phase="explore",
                state={
                    "levels": levels,
                    "level_graph_edges": level_graph_edges(levels),
                    "max_flow": display(max_flow),
                    "flow_table": flow_table(),
                    "residual_network": residual_network(),
                },
            )

            if levels.get(sink, -1) < 0:
                break

            while True:
                path, bottleneck = dfs_path(levels)
                if not path:
                    break

                path_nodes = [path[0][0]] + [step[1] for step in path]
                visual_path_edges = [edge_ids[key] for _, _, key, direction, _ in path if direction == "forward" and key in edge_ids]
                structured_path_edges = path_edges(path, bottleneck)

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

                yield Step(
                    action=StepAction.MARK_PATH,
                    target_type="node",
                    target_id="",
                    value={"nodes": path_nodes, "edges": visual_path_edges},
                    message=f"Send blocking-flow unit {bottleneck:g} through {' -> '.join(path_nodes)}",
                    phase="relax",
                    state={
                        "levels": levels,
                        "level_graph_edges": level_graph_edges(levels),
                        "augmenting_path": path_nodes,
                        "augmenting_path_edges": structured_path_edges,
                        "bottleneck": display(bottleneck),
                        "bottleneck_edges": [edge for edge in structured_path_edges if edge["bottleneck"]],
                        "max_flow": display(max_flow),
                        "flow_table": flow_table(),
                        "residual_network": residual_network(),
                        "augmentations": list(augmentations),
                    },
                )

                for key in capacities:
                    yield Step(
                        action=StepAction.UPDATE_EDGE_LABEL,
                        target_type="edge",
                        target_id=edge_ids[key],
                        value=f"{flow[key]:g}/{capacities[key]:g}",
                        message=f"Flow on {key[0]} -> {key[1]} is {flow[key]:g}/{capacities[key]:g}",
                        phase="relax",
                        state={
                            "levels": levels,
                            "level_graph_edges": level_graph_edges(levels),
                            "max_flow": display(max_flow),
                            "flow_table": flow_table(),
                            "residual_network": residual_network(),
                        },
                    )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Dinic complete. Max flow = {max_flow:g}",
            phase="result",
            state={
                "max_flow": display(max_flow),
                "flow_table": flow_table(),
                "residual_network": residual_network(),
                "augmentations": augmentations,
            },
        )

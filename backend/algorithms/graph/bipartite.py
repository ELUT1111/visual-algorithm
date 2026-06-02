"""Bipartite graph detection with BFS coloring."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BipartiteAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="bipartite",
            category="graph",
            description="Check whether an undirected graph is bipartite",
            emoji="🎨",
            parameters=[],
            requires_undirected=True,
            time_complexity="O(V + E)",
            space_complexity="O(V)",
            use_cases=[
                "Two-coloring graphs",
                "Matching problems",
                "Scheduling with incompatibility constraints",
                "Detecting odd cycles",
            ],
            pseudocode=(
                "function IsBipartite(graph):\n"
                "    for each uncolored vertex s:\n"
                "        color[s] = 0\n"
                "        BFS from s\n"
                "        for each edge u-v:\n"
                "            if v uncolored: color[v] = 1 - color[u]\n"
                "            else if color[v] == color[u]: return false\n"
                "    return true"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        adjacency: dict[str, list[tuple[str, str]]] = {node.id: [] for node in graph.nodes}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            adjacency.setdefault(edge.target, []).append((edge.source, edge_id))

        colors: dict[str, int] = {}
        palette = {0: "#22d3ee", 1: "#fbbf24"}

        def state(queue: list[str] | None = None) -> dict:
            return {
                "queue": queue or [],
                "color": {node_id: ("A" if color == 0 else "B") for node_id, color in colors.items()},
            }

        for node in graph.nodes:
            if node.id in colors:
                continue

            colors[node.id] = 0
            queue = deque([node.id])

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node.id,
                value=palette[0],
                message=f"Start BFS component at {node.id}; assign color A",
                phase="init",
                state=state(list(queue)),
            )

            while queue:
                current = queue.popleft()

                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=current,
                    value=palette[colors[current]],
                    message=f"Process {current}",
                    phase="explore",
                    state=state(list(queue)),
                )

                for neighbor, edge_id in adjacency.get(current, []):
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        value="exploring",
                        message=f"Check edge {current} -- {neighbor}",
                        phase="explore",
                        state=state(list(queue)),
                    )

                    if neighbor not in colors:
                        colors[neighbor] = 1 - colors[current]
                        queue.append(neighbor)
                        yield Step(
                            action=StepAction.SET_NODE_COLOR,
                            target_type="node",
                            target_id=neighbor,
                            value=palette[colors[neighbor]],
                            message=f"Assign {neighbor} to color {'A' if colors[neighbor] == 0 else 'B'}",
                            phase="relax",
                            state=state(list(queue)),
                        )
                    elif colors[neighbor] == colors[current]:
                        yield Step(
                            action=StepAction.MARK_PATH,
                            target_type="node",
                            target_id="",
                            value=[current, neighbor],
                            message=f"Conflict: {current} and {neighbor} have the same color",
                            phase="result",
                            state={**state(list(queue)), "conflict": [current, neighbor]},
                        )
                        return

                    yield Step(
                        action=StepAction.UNHIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        message="",
                        phase="explore",
                        state=state(list(queue)),
                    )

        left = sorted([node_id for node_id, color in colors.items() if color == 0])
        right = sorted([node_id for node_id, color in colors.items() if color == 1])
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Graph is bipartite. Partition sizes: {len(left)} and {len(right)}",
            phase="result",
            state={"partition_A": left, "partition_B": right, "color": state()["color"]},
        )

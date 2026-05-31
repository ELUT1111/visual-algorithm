"""Connected components for graphs."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class ConnectedComponentsAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="connected_components",
            category="graph",
            description="Find weakly connected components",
            emoji="🧩",
            parameters=[],
            time_complexity="O(V + E)",
            space_complexity="O(V)",
            use_cases=[
                "Finding isolated clusters",
                "Social network group discovery",
                "Preprocessing before MST or traversal",
                "Weak components in directed graphs",
            ],
            pseudocode=(
                "function ConnectedComponents(graph):\n"
                "    visited = empty set\n"
                "    for each vertex v:\n"
                "        if v not visited:\n"
                "            start BFS/DFS from v\n"
                "            all reached vertices form one component"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        adjacency: dict[str, list[tuple[str, str]]] = {n.id: [] for n in graph.nodes}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            adjacency.setdefault(edge.target, []).append((edge.source, edge_id))

        visited: set[str] = set()
        components: list[list[str]] = []

        for node in graph.nodes:
            if node.id in visited:
                continue

            component: list[str] = []
            queue = deque([node.id])
            visited.add(node.id)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node.id,
                value="current",
                message=f"Start component {len(components) + 1} at {node.id}",
                phase="init",
                state={
                    "queue": list(queue),
                    "current_component": list(component),
                    "components": [list(c) for c in components],
                    "visited": sorted(visited),
                },
            )

            while queue:
                current = queue.popleft()
                component.append(current)

                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=current,
                    value="current",
                    message=f"Process {current}",
                    phase="explore",
                    state={
                        "queue": list(queue),
                        "current_component": list(component),
                        "components": [list(c) for c in components],
                        "visited": sorted(visited),
                    },
                )

                for neighbor, edge_id in adjacency.get(current, []):
                    if neighbor in visited:
                        continue

                    visited.add(neighbor)
                    queue.append(neighbor)

                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        value="exploring",
                        message=f"Reach {neighbor} from {current}",
                        phase="explore",
                        state={
                            "queue": list(queue),
                            "current_component": list(component),
                            "components": [list(c) for c in components],
                            "visited": sorted(visited),
                        },
                    )

                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=neighbor,
                        value="exploring",
                        message=f"Enqueue {neighbor}",
                        phase="explore",
                        state={
                            "queue": list(queue),
                            "current_component": list(component),
                            "components": [list(c) for c in components],
                            "visited": sorted(visited),
                        },
                    )

                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=current,
                    value="visited",
                    message=f"Add {current} to component {len(components) + 1}",
                    phase="finalize",
                    state={
                        "queue": list(queue),
                        "current_component": list(component),
                        "components": [list(c) for c in components],
                        "visited": sorted(visited),
                    },
                )

            components.append(component)

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Component {len(components)}: {', '.join(component)}",
                phase="finalize",
                state={
                    "queue": [],
                    "current_component": [],
                    "components": [list(c) for c in components],
                    "visited": sorted(visited),
                },
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Found {len(components)} connected component(s)",
            phase="result",
            state={"components": [list(c) for c in components], "visited": sorted(visited)},
        )

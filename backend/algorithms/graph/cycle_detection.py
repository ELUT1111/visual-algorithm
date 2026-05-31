"""Cycle detection for directed and undirected graphs."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class CycleDetectionAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="cycle_detection",
            category="graph",
            description="Detect whether a graph contains a cycle",
            emoji="🔁",
            parameters=[],
            time_complexity="O(V + E)",
            space_complexity="O(V)",
            use_cases=[
                "DAG validation",
                "Dependency analysis",
                "Detecting invalid prerequisites",
                "Finding cycles in network topology",
            ],
            pseudocode=(
                "function HasCycle(graph):\n"
                "    if graph is directed:\n"
                "        use DFS colors: white, gray, black\n"
                "        a gray neighbor means a back edge and cycle\n"
                "    else:\n"
                "        DFS with parent tracking\n"
                "        a visited neighbor that is not parent means cycle"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        adjacency: dict[str, list[tuple[str, str]]] = {n.id: [] for n in graph.nodes}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            if not graph.directed:
                adjacency.setdefault(edge.target, []).append((edge.source, edge_id))

        if graph.directed:
            colors = {node.id: "white" for node in graph.nodes}
            stack: list[str] = []

            def dfs(node_id: str) -> Generator[Step, None, bool]:
                colors[node_id] = "gray"
                stack.append(node_id)
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=node_id,
                    value="current",
                    message=f"Enter {node_id}; mark gray",
                    phase="explore",
                    state={"mode": "directed", "stack": list(stack), "colors": dict(colors)},
                )

                for neighbor, edge_id in adjacency.get(node_id, []):
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        value="exploring",
                        message=f"Inspect edge {node_id} -> {neighbor}",
                        phase="explore",
                        state={"mode": "directed", "stack": list(stack), "colors": dict(colors)},
                    )

                    if colors.get(neighbor) == "gray":
                        cycle_start = stack.index(neighbor) if neighbor in stack else 0
                        cycle = stack[cycle_start:] + [neighbor]
                        yield Step(
                            action=StepAction.MARK_PATH,
                            target_type="node",
                            target_id="",
                            value=cycle,
                            message=f"Back edge to gray node {neighbor}; cycle found: {' -> '.join(cycle)}",
                            phase="result",
                            state={"mode": "directed", "stack": list(stack), "colors": dict(colors), "cycle": cycle},
                        )
                        return True

                    if colors.get(neighbor) == "white":
                        found = yield from dfs(neighbor)
                        if found:
                            return True

                    yield Step(
                        action=StepAction.UNHIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        message="",
                        phase="explore",
                        state={"mode": "directed", "stack": list(stack), "colors": dict(colors)},
                    )

                colors[node_id] = "black"
                stack.pop()
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=node_id,
                    value="visited",
                    message=f"Leave {node_id}; mark black",
                    phase="finalize",
                    state={"mode": "directed", "stack": list(stack), "colors": dict(colors)},
                )
                return False

            for node in graph.nodes:
                if colors[node.id] == "white":
                    found = yield from dfs(node.id)
                    if found:
                        return

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="No directed cycle found",
                phase="result",
                state={"mode": "directed", "stack": [], "colors": dict(colors), "cycle": []},
            )
            return

        visited: set[str] = set()
        parent: dict[str, str | None] = {}

        def dfs_undirected(node_id: str, from_id: str | None) -> Generator[Step, None, bool]:
            visited.add(node_id)
            parent[node_id] = from_id
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="current",
                message=f"Visit {node_id}",
                phase="explore",
                state={"mode": "undirected", "visited": sorted(visited), "parent": dict(parent)},
            )

            for neighbor, edge_id in adjacency.get(node_id, []):
                if neighbor == from_id:
                    continue

                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Inspect edge {node_id} -- {neighbor}",
                    phase="explore",
                    state={"mode": "undirected", "visited": sorted(visited), "parent": dict(parent)},
                )

                if neighbor in visited:
                    cycle = [node_id, neighbor]
                    yield Step(
                        action=StepAction.MARK_PATH,
                        target_type="node",
                        target_id="",
                        value=cycle,
                        message=f"Visited neighbor {neighbor} is not the parent; cycle found",
                        phase="result",
                        state={"mode": "undirected", "visited": sorted(visited), "parent": dict(parent), "cycle": cycle},
                    )
                    return True

                found = yield from dfs_undirected(neighbor, node_id)
                if found:
                    return True

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="explore",
                    state={"mode": "undirected", "visited": sorted(visited), "parent": dict(parent)},
                )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="visited",
                message=f"Finished {node_id}",
                phase="finalize",
                state={"mode": "undirected", "visited": sorted(visited), "parent": dict(parent)},
            )
            return False

        for node in graph.nodes:
            if node.id not in visited:
                found = yield from dfs_undirected(node.id, None)
                if found:
                    return

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="No undirected cycle found",
            phase="result",
            state={"mode": "undirected", "visited": sorted(visited), "parent": dict(parent), "cycle": []},
        )

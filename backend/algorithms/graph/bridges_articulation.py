"""Bridge and articulation point detection for undirected graphs."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BridgesArticulationAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="bridges_articulation",
            category="graph",
            description="Find bridges and articulation points with DFS low-link values",
            emoji="🌉",
            parameters=[],
            requires_undirected=True,
            time_complexity="O(V + E)",
            space_complexity="O(V)",
            use_cases=[
                "Network reliability analysis",
                "Critical road or cable detection",
                "Graph biconnectivity",
                "Finding single points of failure",
            ],
            pseudocode=(
                "function DFS(u):\n"
                "    disc[u] = low[u] = time++\n"
                "    for each neighbor v:\n"
                "        if v unvisited:\n"
                "            parent[v] = u; DFS(v); low[u] = min(low[u], low[v])\n"
                "            if low[v] > disc[u]: edge u-v is a bridge\n"
                "            if root has >1 child or low[v] >= disc[u]: u is articulation\n"
                "        else if v != parent[u]: low[u] = min(low[u], disc[v])"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        adjacency: dict[str, list[tuple[str, str]]] = {node.id: [] for node in graph.nodes}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            adjacency.setdefault(edge.target, []).append((edge.source, edge_id))

        time = 0
        disc: dict[str, int] = {}
        low: dict[str, int] = {}
        parent: dict[str, str | None] = {node.id: None for node in graph.nodes}
        bridges: list[dict[str, str]] = []
        articulation: set[str] = set()
        stack: list[str] = []

        def state() -> dict:
            return {
                "stack": list(stack),
                "disc": dict(disc),
                "low": dict(low),
                "parent": {k: v for k, v in parent.items() if v is not None},
                "bridges": list(bridges),
                "articulation_points": sorted(articulation),
            }

        def dfs(node_id: str, root: str) -> Generator[Step, None, None]:
            nonlocal time
            disc[node_id] = time
            low[node_id] = time
            time += 1
            child_count = 0
            stack.append(node_id)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="current",
                message=f"Visit {node_id}: disc={disc[node_id]}, low={low[node_id]}",
                phase="explore",
                state=state(),
            )

            for neighbor, edge_id in adjacency.get(node_id, []):
                if neighbor == parent[node_id]:
                    continue

                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Inspect edge {node_id} -- {neighbor}",
                    phase="explore",
                    state=state(),
                )

                if neighbor not in disc:
                    parent[neighbor] = node_id
                    child_count += 1
                    yield from dfs(neighbor, root)

                    low[node_id] = min(low[node_id], low[neighbor])
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="node",
                        target_id=node_id,
                        message=f"After {neighbor}, low[{node_id}] = {low[node_id]}",
                        phase="relax",
                        state=state(),
                    )

                    if low[neighbor] > disc[node_id]:
                        bridges.append({"edge": f"{node_id}-{neighbor}", "from": node_id, "to": neighbor})
                        yield Step(
                            action=StepAction.SET_EDGE_COLOR,
                            target_type="edge",
                            target_id=edge_id,
                            value="path",
                            message=f"Bridge found: {node_id} -- {neighbor}",
                            phase="result",
                            state=state(),
                        )

                    if (node_id == root and child_count > 1) or (
                        node_id != root and low[neighbor] >= disc[node_id]
                    ):
                        articulation.add(node_id)
                        yield Step(
                            action=StepAction.SET_NODE_COLOR,
                            target_type="node",
                            target_id=node_id,
                            value="path",
                            message=f"Articulation point found: {node_id}",
                            phase="result",
                            state=state(),
                        )
                else:
                    low[node_id] = min(low[node_id], disc[neighbor])
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="node",
                        target_id=node_id,
                        message=f"Back edge to {neighbor}; low[{node_id}] = {low[node_id]}",
                        phase="relax",
                        state=state(),
                    )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="explore",
                    state=state(),
                )

            stack.pop()
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="visited",
                message=f"Finish {node_id}",
                phase="finalize",
                state=state(),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Start DFS low-link scan",
            phase="init",
            state=state(),
        )

        for node in graph.nodes:
            if node.id not in disc:
                yield from dfs(node.id, node.id)

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Found {len(bridges)} bridge(s) and {len(articulation)} articulation point(s)",
            phase="result",
            state=state(),
        )

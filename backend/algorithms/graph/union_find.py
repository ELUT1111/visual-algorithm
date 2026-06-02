"""Union-Find / Disjoint Set Union visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class UnionFindAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="union_find",
            category="graph",
            description="Build disjoint sets by unioning graph edges",
            emoji="🧱",
            parameters=[],
            requires_undirected=True,
            time_complexity="O((V + E) alpha(V))",
            space_complexity="O(V)",
            use_cases=[
                "Connected components",
                "Kruskal's minimum spanning tree",
                "Cycle detection in undirected graphs",
                "Dynamic connectivity",
            ],
            pseudocode=(
                "function UnionFind(graph):\n"
                "    make_set(v) for each vertex v\n"
                "    for each edge (u, v):\n"
                "        if find(u) != find(v): union(u, v)\n"
                "        else: edge forms a cycle"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        parent = {node.id: node.id for node in graph.nodes}
        rank = {node.id: 0 for node in graph.nodes}

        def find(node_id: str) -> str:
            if parent[node_id] != node_id:
                parent[node_id] = find(parent[node_id])
            return parent[node_id]

        def components() -> list[list[str]]:
            groups: dict[str, list[str]] = {}
            for node_id in parent:
                root = find(node_id)
                groups.setdefault(root, []).append(node_id)
            return [sorted(group) for group in groups.values()]

        def state() -> dict:
            return {
                "parent": dict(parent),
                "rank": dict(rank),
                "components": components(),
            }

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Initialize each node as its own set",
            phase="init",
            state=state(),
        )

        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            root_u = find(edge.source)
            root_v = find(edge.target)

            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_id,
                value="exploring",
                message=f"Check edge {edge.source} -- {edge.target}: roots {root_u}, {root_v}",
                phase="explore",
                state=state(),
            )

            if root_u == root_v:
                yield Step(
                    action=StepAction.SET_EDGE_COLOR,
                    target_type="edge",
                    target_id=edge_id,
                    value="skipped",
                    message=f"{edge.source} and {edge.target} are already connected; edge would form a cycle",
                    phase="finalize",
                    state=state(),
                )
                continue

            if rank[root_u] < rank[root_v]:
                root_u, root_v = root_v, root_u
            parent[root_v] = root_u
            if rank[root_u] == rank[root_v]:
                rank[root_u] += 1

            yield Step(
                action=StepAction.SET_EDGE_COLOR,
                target_type="edge",
                target_id=edge_id,
                value="mst",
                message=f"Union sets: parent[{root_v}] = {root_u}",
                phase="relax",
                state=state(),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Union-Find complete. Components: {len(components())}",
            phase="result",
            state=state(),
        )

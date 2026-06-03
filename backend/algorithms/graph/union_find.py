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
        find_traces: list[dict] = []
        compression_updates: list[dict] = []
        union_trace: list[dict] = []
        rank_updates: list[dict] = []

        def find(node_id: str, *, compress: bool = True) -> tuple[str, dict]:
            path = [node_id]
            cursor = node_id
            while parent[cursor] != cursor:
                cursor = parent[cursor]
                path.append(cursor)
            root = cursor
            updates = []
            if compress:
                for item in path[:-1]:
                    before = parent[item]
                    if before != root:
                        parent[item] = root
                        update = {"node": item, "from": before, "to": root}
                        updates.append(update)
                        compression_updates.append(update)
            trace = {"node": node_id, "path": path, "root": root, "compressed": updates}
            find_traces.append(trace)
            return root, trace

        def components() -> list[list[str]]:
            groups: dict[str, list[str]] = {}
            for node_id in parent:
                cursor = node_id
                while parent[cursor] != cursor:
                    cursor = parent[cursor]
                root = cursor
                groups.setdefault(root, []).append(node_id)
            return [sorted(group) for group in groups.values()]

        def state() -> dict:
            return {
                "parent": dict(parent),
                "rank": dict(rank),
                "components": components(),
                "find_traces": list(find_traces),
                "compression_updates": list(compression_updates),
                "union_trace": list(union_trace),
                "rank_updates": list(rank_updates),
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
            root_u, trace_u = find(edge.source)
            root_v, trace_v = find(edge.target)

            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_id,
                value="exploring",
                message=f"Check edge {edge.source} -- {edge.target}: roots {root_u}, {root_v}",
                phase="explore",
                state={**state(), "current_edge": edge_id, "find_trace": [trace_u, trace_v]},
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

            before_parent = dict(parent)
            before_rank = dict(rank)
            if rank[root_u] < rank[root_v]:
                root_u, root_v = root_v, root_u
            parent[root_v] = root_u
            rank_changed = False
            if rank[root_u] == rank[root_v]:
                rank[root_u] += 1
                rank_changed = True
                rank_updates.append({"root": root_u, "from": before_rank[root_u], "to": rank[root_u]})
            union_event = {
                "edge": edge_id,
                "attached_root": root_v,
                "new_parent": root_u,
                "rank_rule": "attach lower rank under higher rank" if before_rank[root_u] != before_rank[root_v] else "equal rank; promote new root",
                "before_parent": before_parent,
                "after_parent": dict(parent),
                "before_rank": before_rank,
                "after_rank": dict(rank),
                "rank_changed": rank_changed,
            }
            union_trace.append(union_event)

            yield Step(
                action=StepAction.SET_EDGE_COLOR,
                target_type="edge",
                target_id=edge_id,
                value="mst",
                message=f"Union by rank: parent[{root_v}] = {root_u}",
                phase="relax",
                state={**state(), "current_union": union_event},
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Union-Find complete. Components: {len(components())}",
            phase="result",
            state=state(),
        )

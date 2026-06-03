"""Kruskal's minimum spanning tree algorithm with DSU optimization state."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


class UnionFind:
    def __init__(self, elements):
        self.parent = {element: element for element in elements}
        self.rank = {element: 0 for element in elements}
        self.find_traces: list[dict] = []
        self.compression_updates: list[dict] = []
        self.union_trace: list[dict] = []
        self.rank_updates: list[dict] = []

    def find(self, node_id: str) -> tuple[str, dict]:
        path = [node_id]
        cursor = node_id
        while self.parent[cursor] != cursor:
            cursor = self.parent[cursor]
            path.append(cursor)

        root = cursor
        updates = []
        for item in path[:-1]:
            before = self.parent[item]
            if before != root:
                self.parent[item] = root
                update = {"node": item, "from": before, "to": root}
                updates.append(update)
                self.compression_updates.append(update)

        trace = {"node": node_id, "path": path, "root": root, "compressed": updates}
        self.find_traces.append(trace)
        return root, trace

    def union(self, source: str, target: str, edge_id: str) -> tuple[bool, dict]:
        root_source, source_trace = self.find(source)
        root_target, target_trace = self.find(target)
        if root_source == root_target:
            return False, {
                "edge": edge_id,
                "root_source": root_source,
                "root_target": root_target,
                "find_trace": [source_trace, target_trace],
                "cycle": True,
            }

        before_parent = dict(self.parent)
        before_rank = dict(self.rank)
        if self.rank[root_source] < self.rank[root_target]:
            root_source, root_target = root_target, root_source

        self.parent[root_target] = root_source
        rank_changed = False
        if self.rank[root_source] == self.rank[root_target]:
            self.rank[root_source] += 1
            rank_changed = True
            self.rank_updates.append({"root": root_source, "from": before_rank[root_source], "to": self.rank[root_source]})

        event = {
            "edge": edge_id,
            "attached_root": root_target,
            "new_parent": root_source,
            "rank_rule": "attach lower rank under higher rank" if before_rank[root_source] != before_rank[root_target] else "equal rank; promote new root",
            "before_parent": before_parent,
            "after_parent": dict(self.parent),
            "before_rank": before_rank,
            "after_rank": dict(self.rank),
            "rank_changed": rank_changed,
            "find_trace": [source_trace, target_trace],
            "cycle": False,
        }
        self.union_trace.append(event)
        return True, event

    def components(self) -> list[list[str]]:
        groups: dict[str, list[str]] = {}
        for node_id in self.parent:
            cursor = node_id
            while self.parent[cursor] != cursor:
                cursor = self.parent[cursor]
            groups.setdefault(cursor, []).append(node_id)
        return [sorted(group) for group in groups.values()]

    def state(self) -> dict:
        return {
            "parent": dict(self.parent),
            "rank": dict(self.rank),
            "components": self.components(),
            "find_traces": list(self.find_traces),
            "compression_updates": list(self.compression_updates),
            "union_trace": list(self.union_trace),
            "rank_updates": list(self.rank_updates),
        }


@registry.register
class KruskalAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="kruskal",
            category="graph",
            description="Find minimum spanning tree using Kruskal's algorithm",
            emoji="MST",
            parameters=[],
            requires_weighted=True,
            requires_undirected=True,
            time_complexity="O(E log E)",
            space_complexity="O(V + E)",
            use_cases=[
                "Network design",
                "Clustering",
                "Image segmentation",
                "Approximation algorithms",
            ],
            pseudocode=(
                "sort all edges by weight\n"
                "make_set(v) for each vertex\n"
                "for each edge (u, v, w):\n"
                "    if find(u) != find(v):\n"
                "        union by rank\n"
                "        add edge to MST\n"
                "    else skip edge\n"
                "find uses path compression"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        edges = sorted(graph.edges, key=lambda edge: edge.weight)
        sorted_edges = [
            {"id": edge.id or f"{edge.source}-{edge.target}", "source": edge.source, "target": edge.target, "weight": edge.weight}
            for edge in edges
        ]

        uf = UnionFind(node_ids)
        mst_edges: list[tuple[str, str, float]] = []
        total_weight = 0

        def state(extra: dict | None = None) -> dict:
            payload = {
                **uf.state(),
                "sorted_edges": sorted_edges,
                "mst_edges": list(mst_edges),
                "total_weight": total_weight,
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Start Kruskal: {len(edges)} edges sorted by weight",
            phase="init",
            state=state(),
        )

        for edge in edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_id,
                value="exploring",
                message=f"Sorted edge {edge.source} -- {edge.target} (weight={edge.weight})",
                phase="init",
                state=state({"current_edge": edge_id}),
            )
            yield Step(
                action=StepAction.UNHIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_id,
                message="",
                phase="init",
                state=state({"current_edge": edge_id}),
            )

        for edge in edges:
            source, target = edge.source, edge.target
            edge_id = edge.id or f"{source}-{target}"

            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_id,
                value="current",
                message=f"Check edge {source} -- {target} (weight={edge.weight})",
                phase="explore",
                state=state({"current_edge": edge_id}),
            )

            added, union_event = uf.union(source, target, edge_id)
            if added:
                mst_edges.append((source, target, edge.weight))
                total_weight += edge.weight
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="mst",
                    message=f"Add {source} -- {target}; union by rank attaches {union_event['attached_root']} to {union_event['new_parent']}",
                    phase="relax",
                    state=state({"current_union": union_event}),
                )
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=source,
                    value="mst",
                    message="",
                    phase="relax",
                    state=state({"current_union": union_event}),
                )
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=target,
                    value="mst",
                    message="",
                    phase="relax",
                    state=state({"current_union": union_event}),
                )
                if len(mst_edges) == len(node_ids) - 1:
                    break
            else:
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="skipped",
                    message=f"Skip {source} -- {target}; both endpoints already have root {union_event['root_source']}",
                    phase="relax",
                    state=state({"cycle_check": union_event}),
                )
                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                    state=state({"cycle_check": union_event}),
                )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Kruskal complete: total weight {total_weight}, edges {len(mst_edges)}",
            phase="result",
            state=state(),
        )

"""Kruskal's Minimum Spanning Tree algorithm."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


class UnionFind:
    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in elements}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


@registry.register
class KruskalAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="kruskal",
            category="graph",
            description="Find minimum spanning tree using Kruskal's algorithm",
            emoji="🔗",
            parameters=[],
            requires_weighted=True,
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [n.id for n in graph.nodes]
        if not node_ids:
            return

        # Sort edges by weight
        edges = sorted(graph.edges, key=lambda e: e.weight)

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Starting Kruskal's MST. {len(edges)} edges sorted by weight.",
            phase="init",
        )

        # Show sorted edges
        for e in edges:
            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=e.id or f"{e.source}-{e.target}",
                value="exploring",
                message=f"Edge: {e.source} — {e.target} (weight={e.weight})",
                phase="init",
            )
            yield Step(
                action=StepAction.UNHIGHLIGHT_EDGE,
                target_type="edge",
                target_id=e.id or f"{e.source}-{e.target}",
                message="",
                phase="init",
            )

        uf = UnionFind(node_ids)
        mst_edges = []
        total_weight = 0

        for edge in edges:
            u, v = edge.source, edge.target
            edge_id = edge.id or f"{u}-{v}"

            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_id,
                value="current",
                message=f"Checking edge {u} — {v} (weight={edge.weight})",
                phase="explore",
            )

            if uf.union(u, v):
                # Edge added to MST
                mst_edges.append((u, v, edge.weight))
                total_weight += edge.weight

                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="mst",
                    message=f"Added to MST! {u} — {v} (weight={edge.weight})",
                    phase="explore",
                )

                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=u,
                    value="mst",
                    message="",
                    phase="explore",
                )

                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=v,
                    value="mst",
                    message="",
                    phase="explore",
                )

                if len(mst_edges) == len(node_ids) - 1:
                    break
            else:
                # Would create cycle
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="skipped",
                    message=f"Skipped! {u} — {v} would create a cycle",
                    phase="relax",
                )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                )

        # Summary
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Kruskal's MST complete! Total weight: {total_weight}, Edges: {len(mst_edges)}",
            phase="result",
        )

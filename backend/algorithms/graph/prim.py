"""Prim's Minimum Spanning Tree algorithm."""
from __future__ import annotations

import heapq
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class PrimAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="prim",
            category="graph",
            description="Find minimum spanning tree using Prim's algorithm",
            emoji="🌳",
            parameters=[
                {"name": "source", "type": "str", "required": False, "default": "", "description": "Start node (optional)"}
            ],
            requires_weighted=True,
            requires_undirected=True,
            time_complexity="O((V + E) log V)",
            space_complexity="O(V)",
            use_cases=[
                "Network design (minimum cable length)",
                "Cluster analysis",
                "Approximation for TSP",
                "Circuit board wiring optimization",
            ],
            pseudocode=(
                "function Prim(graph, source):\n"
                "    inMST = {source}\n"
                "    totalWeight = 0\n"
                "    edges = min-heap of edges from source\n"
                "    while edges is not empty and |inMST| < |V|:\n"
                "        (w, u, v) = edges.extractMin()\n"
                "        if v in inMST: continue\n"
                "        add v to inMST\n"
                "        totalWeight += w\n"
                "        for each edge (v, neighbor, w):\n"
                "            if neighbor not in inMST:\n"
                "                edges.insert(w, v, neighbor)\n"
                "    return totalWeight, inMST"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source", "") or (graph.nodes[0].id if graph.nodes else None)
        if not source:
            return

        # Build adjacency list
        adj: dict[str, list[tuple[float, str, str]]] = {n.id: [] for n in graph.nodes}
        for e in graph.edges:
            adj.setdefault(e.source, []).append((e.weight, e.target, e.id))
            adj.setdefault(e.target, []).append((e.weight, e.source, e.id))

        in_mst = set()
        total_weight = 0
        mst_edges = []

        # Start with source
        in_mst.add(source)
        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="mst",
            message=f"Starting Prim's MST from node {source}",
            phase="init",
        )

        # Add all edges from source to priority queue
        heap = []
        for weight, neighbor, edge_id in adj.get(source, []):
            heapq.heappush(heap, (weight, source, neighbor, edge_id))

        while heap and len(in_mst) < len(graph.nodes):
            weight, u, v, edge_id = heapq.heappop(heap)

            if v in in_mst:
                continue

            # Add v to MST
            in_mst.add(v)
            total_weight += weight
            mst_edges.append((u, v, weight))

            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_id,
                value="mst",
                message=f"Adding edge {u} — {v} (weight={weight}) to MST",
                phase="explore",
            )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=v,
                value="mst",
                message=f"Node {v} added to MST (total weight={total_weight})",
                phase="explore",
            )

            # Add edges from v to heap
            for w, neighbor, eid in adj.get(v, []):
                if neighbor not in in_mst:
                    heapq.heappush(heap, (w, v, neighbor, eid))

                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=eid,
                        value="exploring",
                        message=f"Considering edge {v} — {neighbor} (weight={w})",
                        phase="relax",
                    )

                    yield Step(
                        action=StepAction.UNHIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=eid,
                        message="",
                        phase="relax",
                    )

        # Summary
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"MST complete! Total weight: {total_weight}, Edges: {len(mst_edges)}",
            phase="result",
        )

        # Highlight MST edges
        for u, v, w in mst_edges:
            # Try both directions since vis-network may store edge either way
            edge_id = f"{u}-{v}"
            rev_id = f"{v}-{u}"
            # We yield both; the visualizer/vis-network will handle whichever exists
            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_id,
                value="path",
                message=f"MST edge: {u} — {v} (weight={w})",
                phase="result",
            )
            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=rev_id,
                value="path",
                message="",
                phase="result",
            )

"""Gomory-Hu tree construction for all-pairs minimum cuts."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class GomoryHuTreeAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="gomory_hu_tree",
            category="graph",
            description="Build a cut-equivalent tree that represents all-pairs min-cuts in an undirected graph",
            emoji="GH",
            parameters=[],
            requires_weighted=True,
            requires_undirected=True,
            allows_negative_weights=False,
            time_complexity="O(V) max-flow computations",
            space_complexity="O(V + E)",
            use_cases=[
                "All-pairs network reliability queries",
                "Repeated min-cut analysis",
                "Graph clustering by cut strength",
                "Infrastructure bottleneck maps",
            ],
            pseudocode=(
                "initialize every vertex parent to root\n"
                "for each non-root vertex s:\n"
                "    t = parent[s]\n"
                "    compute minimum s-t cut (S, V-S)\n"
                "    reparent vertices whose parent is t and lie in S\n"
                "    if parent[t] lies in S, rotate tree edges\n"
                "    set the cut value on the new tree edge\n"
                "return the cut-equivalent tree"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if len(node_ids) < 2:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="Gomory-Hu tree needs at least two nodes",
                phase="result",
                state={"gomory_hu_tree": [], "cut_iterations": []},
            )
            return

        original_edges: list[dict] = []
        capacities: dict[str, dict[str, float]] = {node_id: {} for node_id in node_ids}
        for edge in graph.edges:
            if edge.source == edge.target:
                continue
            weight = float(edge.weight)
            if weight <= 0:
                continue
            capacities.setdefault(edge.source, {})
            capacities.setdefault(edge.target, {})
            capacities[edge.source][edge.target] = capacities[edge.source].get(edge.target, 0.0) + weight
            capacities[edge.target][edge.source] = capacities[edge.target].get(edge.source, 0.0) + weight
            original_edges.append(
                {
                    "id": edge.id or f"{edge.source}-{edge.target}",
                    "source": edge.source,
                    "target": edge.target,
                    "weight": weight,
                }
            )

        def display(value: float | int | str):
            if value == float("inf"):
                return "Infinity"
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return round(value, 3) if isinstance(value, float) else value

        def min_cut(source: str, sink: str) -> tuple[float, set[str], list[dict], list[dict]]:
            residual: dict[str, dict[str, float]] = {node_id: {} for node_id in node_ids}
            for u in node_ids:
                for v, cap in capacities.get(u, {}).items():
                    residual[u][v] = residual[u].get(v, 0.0) + cap

            augmentations: list[dict] = []
            max_flow = 0.0

            while True:
                parent: dict[str, str | None] = {source: None}
                queue = deque([source])
                while queue and sink not in parent:
                    u = queue.popleft()
                    for v, cap in sorted(residual.get(u, {}).items()):
                        if cap > 1e-9 and v not in parent:
                            parent[v] = u
                            queue.append(v)

                if sink not in parent:
                    break

                bottleneck = float("inf")
                cursor = sink
                path = [sink]
                while cursor != source:
                    prev = parent[cursor]
                    if prev is None:
                        break
                    bottleneck = min(bottleneck, residual[prev][cursor])
                    cursor = prev
                    path.append(cursor)
                path.reverse()

                cursor = sink
                while cursor != source:
                    prev = parent[cursor]
                    if prev is None:
                        break
                    residual[prev][cursor] -= bottleneck
                    residual[cursor][prev] = residual[cursor].get(prev, 0.0) + bottleneck
                    cursor = prev

                max_flow += bottleneck
                augmentations.append({"path": path, "bottleneck": display(bottleneck), "flow_after": display(max_flow)})

            reachable: set[str] = set()
            queue = deque([source])
            reachable.add(source)
            while queue:
                u = queue.popleft()
                for v, cap in residual.get(u, {}).items():
                    if cap > 1e-9 and v not in reachable:
                        reachable.add(v)
                        queue.append(v)

            cut_edges = []
            for edge in original_edges:
                source_in = edge["source"] in reachable
                target_in = edge["target"] in reachable
                if source_in != target_in:
                    cut_edges.append(
                        {
                            "edge": edge["id"],
                            "source": edge["source"],
                            "target": edge["target"],
                            "weight": display(edge["weight"]),
                        }
                    )

            return max_flow, reachable, cut_edges, augmentations

        root = node_ids[0]
        parent: dict[str, str] = {node_id: root for node_id in node_ids}
        parent[root] = root
        cut_value: dict[str, float] = {node_id: 0.0 for node_id in node_ids}
        cut_iterations: list[dict] = []

        def tree_edges() -> list[dict]:
            return [
                {"source": node_id, "target": parent[node_id], "cut_value": display(cut_value[node_id])}
                for node_id in node_ids
                if node_id != root
            ]

        def tree_adjacency() -> dict[str, list[tuple[str, float]]]:
            adj: dict[str, list[tuple[str, float]]] = {node_id: [] for node_id in node_ids}
            for row in tree_edges():
                value = float(row["cut_value"])
                adj[row["source"]].append((row["target"], value))
                adj[row["target"]].append((row["source"], value))
            return adj

        def pair_min_cut(u: str, v: str) -> float:
            adj = tree_adjacency()
            queue = deque([(u, float("inf"))])
            seen = {u}
            while queue:
                current, best = queue.popleft()
                if current == v:
                    return best
                for neighbor, value in adj.get(current, []):
                    if neighbor in seen:
                        continue
                    seen.add(neighbor)
                    queue.append((neighbor, min(best, value)))
            return 0.0

        def all_pairs_min_cuts() -> list[dict]:
            rows = []
            for i, u in enumerate(node_ids):
                for v in node_ids[i + 1:]:
                    rows.append({"source": u, "target": v, "min_cut": display(pair_min_cut(u, v))})
            return rows

        def state(extra: dict | None = None) -> dict:
            payload = {
                "root": root,
                "parents": {node_id: parent[node_id] for node_id in node_ids if node_id != root},
                "gomory_hu_tree": tree_edges(),
                "cut_iterations": list(cut_iterations),
                "all_pairs_min_cuts": all_pairs_min_cuts() if len(cut_iterations) == len(node_ids) - 1 else [],
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Start Gomory-Hu tree from root {root}",
            phase="init",
            state=state(),
        )

        for source in node_ids[1:]:
            sink = parent[source]
            value, reachable, cut_edges, augmentations = min_cut(source, sink)
            previous_parent_source = parent[source]
            swapped = False

            reparented = []
            for candidate in node_ids:
                if candidate == source or candidate == root:
                    continue
                if parent[candidate] == sink and candidate in reachable:
                    parent[candidate] = source
                    reparented.append(candidate)

            if sink != root and parent[sink] in reachable:
                parent[source] = parent[sink]
                parent[sink] = source
                cut_value[source] = cut_value[sink]
                cut_value[sink] = value
                swapped = True
            else:
                parent[source] = previous_parent_source
                cut_value[source] = value

            iteration = {
                "source": source,
                "sink": sink,
                "cut_value": display(value),
                "reachable_side": sorted(reachable),
                "cut_edges": cut_edges,
                "augmentations": augmentations,
                "reparented": reparented,
                "swapped": swapped,
            }
            cut_iterations.append(iteration)

            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": sorted(reachable), "edges": [edge["edge"] for edge in cut_edges]},
                message=f"Min-cut {source} vs {sink} has value {display(value)}",
                phase="explore",
                state=state({"current_cut": iteration}),
            )

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Update Gomory-Hu parent pointers after cut {source}-{sink}",
                phase="relax",
                state=state({"current_cut": iteration}),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Gomory-Hu tree complete with {len(node_ids) - 1} tree edges",
            phase="result",
            state=state({"all_pairs_min_cuts": all_pairs_min_cuts()}),
        )

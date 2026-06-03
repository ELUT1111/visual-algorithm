"""Minimum cycle basis for undirected weighted graphs."""
from __future__ import annotations

import heapq
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class MinimumCycleBasisAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="minimum_cycle_basis",
            category="graph",
            description="Find a minimum-weight independent cycle basis in an undirected graph",
            emoji="MCB",
            parameters=[],
            requires_weighted=True,
            requires_undirected=True,
            allows_negative_weights=False,
            time_complexity="O(E * (E log V) + C * E)",
            space_complexity="O(C * E)",
            use_cases=[
                "Network redundancy analysis",
                "Electrical mesh and circuit-loop analysis",
                "Planar graph and topology inspection",
                "Molecular ring-system decomposition",
            ],
            pseudocode=(
                "for each edge e=(u,v):\n"
                "    remove e and find the shortest u-v path\n"
                "    path plus e is a candidate cycle\n"
                "sort candidate cycles by total weight\n"
                "for each candidate cycle:\n"
                "    reduce its edge-incidence vector over GF(2)\n"
                "    if independent, add it to the basis\n"
                "stop after m - n + components cycles"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        edges = []
        for edge in graph.edges:
            if edge.source == edge.target:
                continue
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            edges.append({"id": edge_id, "source": edge.source, "target": edge.target, "weight": float(edge.weight)})

        edge_index = {edge["id"]: index for index, edge in enumerate(edges)}
        adjacency: dict[str, list[dict]] = {node_id: [] for node_id in node_ids}
        for edge in edges:
            adjacency.setdefault(edge["source"], []).append(edge)
            adjacency.setdefault(edge["target"], []).append(
                {"id": edge["id"], "source": edge["target"], "target": edge["source"], "weight": edge["weight"]}
            )

        def display(value: float):
            return int(value) if value == int(value) else round(value, 3)

        def connected_components() -> list[list[str]]:
            seen = set()
            components = []
            for start in node_ids:
                if start in seen:
                    continue
                stack = [start]
                seen.add(start)
                component = []
                while stack:
                    current = stack.pop()
                    component.append(current)
                    for edge in adjacency.get(current, []):
                        neighbor = edge["target"]
                        if neighbor not in seen:
                            seen.add(neighbor)
                            stack.append(neighbor)
                components.append(sorted(component))
            return components

        components = connected_components()
        cycle_rank = max(0, len(edges) - len(node_ids) + len(components))

        def shortest_path_without(source: str, target: str, banned_edge: str) -> dict | None:
            heap = [(0.0, source, [source], [], [])]
            best = {source: 0.0}
            while heap:
                cost, current, nodes_path, edges_path, weights_path = heapq.heappop(heap)
                if cost != best.get(current, float("inf")):
                    continue
                if current == target:
                    return {"nodes": nodes_path, "edges": edges_path, "weights": weights_path, "cost": cost}
                for edge in sorted(adjacency.get(current, []), key=lambda item: (item["weight"], item["target"], item["id"])):
                    if edge["id"] == banned_edge:
                        continue
                    neighbor = edge["target"]
                    if neighbor in nodes_path:
                        continue
                    candidate = cost + edge["weight"]
                    if candidate < best.get(neighbor, float("inf")):
                        best[neighbor] = candidate
                        heapq.heappush(
                            heap,
                            (
                                candidate,
                                neighbor,
                                nodes_path + [neighbor],
                                edges_path + [edge["id"]],
                                weights_path + [edge["weight"]],
                            ),
                        )
            return None

        def cycle_mask(edge_ids: list[str]) -> int:
            mask = 0
            for edge_id in edge_ids:
                mask ^= 1 << edge_index[edge_id]
            return mask

        def cycle_row(cycle: dict, rank: int = 0) -> dict:
            return {
                "rank": rank,
                "nodes": list(cycle["nodes"]),
                "edges": list(cycle["edges"]),
                "weight": display(float(cycle["weight"])),
            }

        candidate_cycles = []
        seen_cycles: set[frozenset[str]] = set()
        for edge in edges:
            path = shortest_path_without(edge["source"], edge["target"], edge["id"])
            if not path:
                continue
            cycle_edges = path["edges"] + [edge["id"]]
            key = frozenset(cycle_edges)
            if key in seen_cycles:
                continue
            seen_cycles.add(key)
            cycle_nodes = path["nodes"] + [edge["source"]]
            candidate_cycles.append(
                {
                    "nodes": cycle_nodes,
                    "edges": cycle_edges,
                    "weight": path["cost"] + edge["weight"],
                    "mask": cycle_mask(cycle_edges),
                    "support_edge": edge["id"],
                }
            )

        candidate_cycles.sort(key=lambda item: (item["weight"], len(item["edges"]), item["edges"]))
        selection_trace: list[dict] = []
        basis: list[dict] = []
        pivots: dict[int, int] = {}

        def state(extra: dict | None = None) -> dict:
            payload = {
                "components": components,
                "cycle_rank": cycle_rank,
                "candidate_cycles": [cycle_row(cycle) for cycle in candidate_cycles],
                "selection_trace": list(selection_trace),
                "minimum_cycle_basis": [cycle_row(cycle, index + 1) for index, cycle in enumerate(basis)],
                "total_weight": display(sum(cycle["weight"] for cycle in basis)),
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Generated {len(candidate_cycles)} candidate cycle(s); basis rank is {cycle_rank}",
            phase="init",
            state=state(),
        )

        for candidate in candidate_cycles:
            reduced = candidate["mask"]
            reductions = []
            for pivot in sorted(pivots.keys(), reverse=True):
                if reduced & (1 << pivot):
                    before = reduced
                    reduced ^= pivots[pivot]
                    reductions.append({"pivot_edge": edges[pivot]["id"], "before": before, "after": reduced})

            independent = reduced != 0
            trace = {
                "cycle": cycle_row(candidate),
                "independent": independent,
                "reductions": reductions,
            }
            if independent:
                pivot = reduced.bit_length() - 1
                pivots[pivot] = reduced
                basis.append(candidate)
                trace["pivot_edge"] = edges[pivot]["id"]
            selection_trace.append(trace)

            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": candidate["nodes"], "edges": candidate["edges"]},
                message=(
                    f"Accept independent cycle of weight {display(candidate['weight'])}"
                    if independent
                    else f"Skip dependent cycle of weight {display(candidate['weight'])}"
                ),
                phase="relax",
                state=state({"current_cycle": trace}),
            )

            if len(basis) == cycle_rank:
                break

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Minimum cycle basis complete with {len(basis)} cycle(s)",
            phase="result",
            state=state(),
        )

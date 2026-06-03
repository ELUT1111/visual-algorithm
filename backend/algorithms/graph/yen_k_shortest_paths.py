"""Yen's algorithm for K shortest loopless paths."""
from __future__ import annotations

import heapq
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class YenKShortestPathsAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="yen_k_shortest_paths",
            category="graph",
            description="Find the K shortest simple paths between two nodes with Yen's algorithm",
            emoji="KSP",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"},
                {"name": "target", "type": "str", "required": True, "description": "Target node ID"},
                {"name": "k", "type": "int", "required": False, "default": 3, "description": "Number of paths to return"},
            ],
            requires_weighted=True,
            allows_negative_weights=False,
            time_complexity="O(K * V * (E + V) log V)",
            space_complexity="O(KV + E)",
            use_cases=[
                "Backup route planning",
                "Network failover analysis",
                "Alternative itinerary generation",
                "Path diversity and resilience studies",
            ],
            pseudocode=(
                "A[0] = shortest_path(source, target)\n"
                "B = candidate min-heap\n"
                "for kth path from 1 to K-1:\n"
                "    for each spur index in A[k-1]:\n"
                "        root = prefix of A[k-1]\n"
                "        remove edges that would duplicate previous roots\n"
                "        remove root nodes except the spur node\n"
                "        spur = shortest_path(spur_node, target)\n"
                "        push root + spur into B\n"
                "    A[k] = minimum candidate from B"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        source = str(params.get("source", "") or "").strip() or node_ids[0]
        target = str(params.get("target", "") or "").strip() or node_ids[-1]
        try:
            k = max(1, int(params.get("k", 3)))
        except (TypeError, ValueError):
            k = 3

        if source not in node_ids or target not in node_ids or source == target:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="Yen K-shortest paths needs distinct source and target nodes in the graph",
                phase="result",
                state={"source": source, "target": target, "k": k, "shortest_paths": [], "candidates": []},
            )
            return

        adjacency: dict[str, list[dict]] = {node_id: [] for node_id in node_ids}
        edge_weight: dict[str, float] = {}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            row = {"to": edge.target, "weight": float(edge.weight), "edge": edge_id, "from": edge.source}
            adjacency.setdefault(edge.source, []).append(row)
            edge_weight[edge_id] = float(edge.weight)
            if not graph.directed:
                adjacency.setdefault(edge.target, []).append(
                    {"to": edge.source, "weight": float(edge.weight), "edge": edge_id, "from": edge.target}
                )

        def display(value: float):
            return int(value) if value == int(value) else round(value, 3)

        def path_row(path: dict) -> dict:
            return {
                "rank": path.get("rank", 0),
                "path": list(path["nodes"]),
                "edges": list(path["edges"]),
                "cost": display(float(path["cost"])),
            }

        def dijkstra_path(
            start: str,
            end: str,
            banned_edges: set[tuple[str, str, str]],
            banned_nodes: set[str],
        ) -> dict | None:
            heap = [(0.0, start, [], [], [])]
            best: dict[str, float] = {start: 0.0}
            while heap:
                cost, current, nodes_path, edges_path, weights_path = heapq.heappop(heap)
                if cost != best.get(current, float("inf")):
                    continue
                next_nodes = nodes_path + [current]
                if current == end:
                    return {
                        "nodes": next_nodes,
                        "edges": edges_path,
                        "weights": weights_path,
                        "cost": cost,
                    }
                for edge in sorted(adjacency.get(current, []), key=lambda item: (item["weight"], item["to"], item["edge"])):
                    neighbor = edge["to"]
                    if neighbor in banned_nodes or neighbor in next_nodes:
                        continue
                    edge_key = (current, neighbor, edge["edge"])
                    if edge_key in banned_edges:
                        continue
                    candidate = cost + edge["weight"]
                    if candidate < best.get(neighbor, float("inf")):
                        best[neighbor] = candidate
                        heapq.heappush(
                            heap,
                            (
                                candidate,
                                neighbor,
                                next_nodes,
                                edges_path + [edge["edge"]],
                                weights_path + [edge["weight"]],
                            ),
                        )
            return None

        def ban_edge(banned_edges: set[tuple[str, str, str]], u: str, v: str, edge_id: str) -> None:
            banned_edges.add((u, v, edge_id))
            if not graph.directed:
                banned_edges.add((v, u, edge_id))

        accepted: list[dict] = []
        candidate_heap: list[tuple[float, tuple[str, ...], int, dict]] = []
        candidate_keys: set[tuple[str, ...]] = set()
        spur_iterations: list[dict] = []
        counter = 0

        first = dijkstra_path(source, target, set(), set())
        if not first:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"No path from {source} to {target}",
                phase="result",
                state={"source": source, "target": target, "k": k, "shortest_paths": [], "candidates": []},
            )
            return

        first["rank"] = 1
        accepted.append(first)

        def state(extra: dict | None = None) -> dict:
            payload = {
                "source": source,
                "target": target,
                "k": k,
                "shortest_paths": [path_row(path) for path in accepted],
                "candidates": [path_row(item[3]) for item in sorted(candidate_heap)],
                "spur_iterations": list(spur_iterations),
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": first["nodes"], "edges": first["edges"]},
            message=f"Initial shortest path: {' -> '.join(first['nodes'])} (cost={display(first['cost'])})",
            phase="init",
            state=state({"current_path": path_row(first)}),
        )

        while len(accepted) < k:
            previous = accepted[-1]
            generated_this_round = 0

            for spur_index in range(len(previous["nodes"]) - 1):
                spur_node = previous["nodes"][spur_index]
                root_nodes = previous["nodes"][: spur_index + 1]
                root_edges = previous["edges"][:spur_index]
                root_weights = previous["weights"][:spur_index]
                root_cost = sum(root_weights)

                banned_edges: set[tuple[str, str, str]] = set()
                for path in accepted:
                    if path["nodes"][: spur_index + 1] == root_nodes and len(path["nodes"]) > spur_index + 1:
                        ban_edge(
                            banned_edges,
                            path["nodes"][spur_index],
                            path["nodes"][spur_index + 1],
                            path["edges"][spur_index],
                        )

                banned_nodes = set(root_nodes[:-1])
                spur_path = dijkstra_path(spur_node, target, banned_edges, banned_nodes)
                iteration = {
                    "base_rank": previous["rank"],
                    "spur_node": spur_node,
                    "root_path": list(root_nodes),
                    "removed_edges": [
                        {"source": u, "target": v, "edge": edge_id}
                        for u, v, edge_id in sorted(banned_edges)
                        if graph.directed or u < v
                    ],
                    "removed_nodes": sorted(banned_nodes),
                    "spur_path": list(spur_path["nodes"]) if spur_path else [],
                }

                if spur_path:
                    total_nodes = root_nodes[:-1] + spur_path["nodes"]
                    total_edges = root_edges + spur_path["edges"]
                    total_weights = root_weights + spur_path["weights"]
                    total_cost = root_cost + spur_path["cost"]
                    key = tuple(total_nodes)
                    if key not in candidate_keys and all(tuple(path["nodes"]) != key for path in accepted):
                        counter += 1
                        candidate = {
                            "rank": 0,
                            "nodes": total_nodes,
                            "edges": total_edges,
                            "weights": total_weights,
                            "cost": total_cost,
                        }
                        candidate_keys.add(key)
                        heapq.heappush(candidate_heap, (total_cost, key, counter, candidate))
                        generated_this_round += 1
                        iteration["candidate"] = path_row(candidate)

                spur_iterations.append(iteration)
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id=spur_node,
                    message=f"Spur at {spur_node} from root {' -> '.join(root_nodes)}",
                    phase="explore",
                    state=state({"current_spur": iteration}),
                )

            if not candidate_heap:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id="",
                    message=f"No more candidate paths after generating {len(accepted)} path(s)",
                    phase="result",
                    state=state({"generated_this_round": generated_this_round}),
                )
                break

            _, key, _, next_path = heapq.heappop(candidate_heap)
            candidate_keys.discard(key)
            next_path["rank"] = len(accepted) + 1
            accepted.append(next_path)

            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": next_path["nodes"], "edges": next_path["edges"]},
                message=(
                    f"Accept path #{next_path['rank']}: {' -> '.join(next_path['nodes'])} "
                    f"(cost={display(next_path['cost'])})"
                ),
                phase="relax",
                state=state({"accepted_path": path_row(next_path), "generated_this_round": generated_this_round}),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Yen complete: found {len(accepted)} path(s) from {source} to {target}",
            phase="result",
            state=state(),
        )

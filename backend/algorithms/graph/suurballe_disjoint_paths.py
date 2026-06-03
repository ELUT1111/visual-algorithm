"""Suurballe-style shortest pair of edge-disjoint paths."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class SuurballeDisjointPathsAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="suurballe_disjoint_paths",
            category="graph",
            description="Find two minimum-total-cost edge-disjoint paths between a source and target",
            emoji="2P",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"},
                {"name": "target", "type": "str", "required": True, "description": "Target node ID"},
            ],
            requires_weighted=True,
            requires_directed=True,
            allows_negative_weights=False,
            time_complexity="O(2 * V * E)",
            space_complexity="O(V + E)",
            use_cases=[
                "Link-disjoint backup routing",
                "Network resilience planning",
                "Dual-path service provisioning",
                "Failure-tolerant dependency routing",
            ],
            pseudocode=(
                "run shortest path from source to target\n"
                "build residual network with unit edge capacities\n"
                "reverse used edges with negative cost\n"
                "run a second shortest augmenting path in the residual network\n"
                "cancel opposite residual edges\n"
                "decompose the remaining flow into two edge-disjoint paths"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        source = str(params.get("source", "") or "").strip() or node_ids[0]
        target = str(params.get("target", "") or "").strip() or node_ids[-1]
        if source not in node_ids or target not in node_ids or source == target:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="Suurballe needs distinct source and target nodes in the graph",
                phase="result",
                state={"source": source, "target": target, "disjoint_paths": [], "total_cost": 0},
            )
            return

        arcs: list[dict] = []
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            arcs.append(
                {
                    "id": edge_id,
                    "source": edge.source,
                    "target": edge.target,
                    "cost": float(edge.weight),
                    "capacity": 1,
                    "flow": 0,
                    "rev": None,
                    "original": True,
                }
            )

        residual: dict[str, list[int]] = {node_id: [] for node_id in node_ids}

        def add_arc(base: dict) -> None:
            forward_index = len(arcs)
            reverse_index = forward_index + 1
            forward = {**base, "rev": reverse_index, "original": True}
            reverse = {
                "id": f"{base['id']}::rev",
                "source": base["target"],
                "target": base["source"],
                "cost": -base["cost"],
                "capacity": 0,
                "flow": 0,
                "rev": forward_index,
                "original": False,
                "base_id": base["id"],
            }
            arcs.append(forward)
            arcs.append(reverse)
            residual.setdefault(forward["source"], []).append(forward_index)
            residual.setdefault(reverse["source"], []).append(reverse_index)

        source_arcs = list(arcs)
        arcs = []
        for arc in source_arcs:
            add_arc(arc)

        def display(value: float):
            return int(value) if value == int(value) else round(value, 3)

        def path_row(path: dict) -> dict:
            return {
                "nodes": list(path["nodes"]),
                "edges": list(path["edges"]),
                "cost": display(float(path["cost"])),
            }

        def shortest_residual_path() -> dict | None:
            distances = {node_id: float("inf") for node_id in node_ids}
            parent: dict[str, int] = {}
            in_queue = {node_id: False for node_id in node_ids}
            distances[source] = 0.0
            queue = deque([source])
            in_queue[source] = True

            while queue:
                current = queue.popleft()
                in_queue[current] = False
                for arc_index in residual.get(current, []):
                    arc = arcs[arc_index]
                    if arc["capacity"] - arc["flow"] <= 0:
                        continue
                    candidate = distances[current] + arc["cost"]
                    if candidate < distances[arc["target"]]:
                        distances[arc["target"]] = candidate
                        parent[arc["target"]] = arc_index
                        if not in_queue[arc["target"]]:
                            queue.append(arc["target"])
                            in_queue[arc["target"]] = True

            if target not in parent:
                return None

            arc_indices = []
            nodes = [target]
            cursor = target
            while cursor != source:
                arc_index = parent[cursor]
                arc = arcs[arc_index]
                arc_indices.append(arc_index)
                cursor = arc["source"]
                nodes.append(cursor)
            arc_indices.reverse()
            nodes.reverse()

            return {
                "nodes": nodes,
                "arc_indices": arc_indices,
                "edges": [arcs[index].get("base_id") or arcs[index]["id"] for index in arc_indices],
                "cost": sum(arcs[index]["cost"] for index in arc_indices),
                "distances": {node_id: display(value) for node_id, value in distances.items() if value != float("inf")},
            }

        augmentations: list[dict] = []
        first_path: dict | None = None

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id=source,
            message=f"Start Suurballe disjoint-path search from {source} to {target}",
            phase="init",
            state={"source": source, "target": target, "residual_augmentations": []},
        )

        for round_index in range(2):
            path = shortest_residual_path()
            if not path:
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id="",
                    message=f"Only {round_index} edge-disjoint path(s) exist from {source} to {target}",
                    phase="result",
                    state={
                        "source": source,
                        "target": target,
                        "first_path": path_row(first_path) if first_path else None,
                        "residual_augmentations": augmentations,
                        "disjoint_paths": [],
                        "total_cost": 0,
                    },
                )
                return

            for arc_index in path["arc_indices"]:
                arc = arcs[arc_index]
                arc["flow"] += 1
                arcs[arc["rev"]]["flow"] -= 1

            row = path_row(path)
            row["round"] = round_index + 1
            row["residual_distances"] = path["distances"]
            augmentations.append(row)
            if round_index == 0:
                first_path = path

            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": path["nodes"], "edges": path["edges"]},
                message=(
                    f"Residual shortest path #{round_index + 1}: "
                    f"{' -> '.join(path['nodes'])} (cost={display(path['cost'])})"
                ),
                phase="explore" if round_index == 0 else "relax",
                state={
                    "source": source,
                    "target": target,
                    "first_path": path_row(first_path) if first_path else None,
                    "residual_augmentations": list(augmentations),
                },
            )

        flow_adj: dict[str, list[dict]] = {node_id: [] for node_id in node_ids}
        for arc in arcs:
            if arc["original"] and arc["flow"] > 0:
                flow_adj.setdefault(arc["source"], []).append(arc)

        disjoint_paths = []
        for _ in range(2):
            current = source
            nodes = [source]
            edges = []
            cost = 0.0
            while current != target:
                choices = sorted(flow_adj.get(current, []), key=lambda item: (item["cost"], item["target"], item["id"]))
                if not choices:
                    break
                arc = choices.pop(0)
                flow_adj[current] = choices
                edges.append(arc["id"])
                cost += arc["cost"]
                current = arc["target"]
                nodes.append(current)
            if nodes[-1] == target:
                disjoint_paths.append({"nodes": nodes, "edges": edges, "cost": cost})

        total_cost = sum(path["cost"] for path in disjoint_paths)
        final_state = {
            "source": source,
            "target": target,
            "first_path": path_row(first_path) if first_path else None,
            "residual_augmentations": augmentations,
            "disjoint_paths": [path_row(path) for path in disjoint_paths],
            "total_cost": display(total_cost),
            "shared_edges": [],
        }

        for path in disjoint_paths:
            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": path["nodes"], "edges": path["edges"]},
                message=f"Disjoint path: {' -> '.join(path['nodes'])} (cost={display(path['cost'])})",
                phase="result",
                state=final_state,
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Suurballe complete: two edge-disjoint paths with total cost {display(total_cost)}",
            phase="result",
            state=final_state,
        )

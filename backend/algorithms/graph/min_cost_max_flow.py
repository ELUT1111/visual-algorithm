"""Min-cost max-flow visualization using SPFA shortest augmenting paths."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class MinCostMaxFlowAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="min_cost_max_flow",
            category="graph",
            description="Send maximum flow with minimum total cost using residual shortest paths",
            emoji="MC",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"},
                {"name": "target", "type": "str", "required": True, "description": "Sink node ID"},
            ],
            requires_weighted=True,
            requires_directed=True,
            allows_negative_weights=False,
            time_complexity="O(FVE) with SPFA augmenting paths",
            space_complexity="O(E)",
            use_cases=[
                "Minimum-cost routing",
                "Transportation planning",
                "Assignment with capacities",
                "Flow optimization",
            ],
            pseudocode=(
                "while shortest residual path from source to sink exists:\n"
                "    bottleneck = minimum residual capacity on path\n"
                "    augment flow along path\n"
                "    total_cost += bottleneck * path_cost"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source")
        sink = params.get("target")
        if not source or not sink or source == sink:
            return

        edges: list[dict] = []
        adjacency: dict[str, list[int]] = {node.id: [] for node in graph.nodes}

        def add_edge(u: str, v: str, cap: float, cost: float, edge_id: str) -> None:
            forward = {"u": u, "v": v, "cap": cap, "cost": cost, "flow": 0.0, "rev": len(edges) + 1, "id": edge_id, "forward": True}
            reverse = {"u": v, "v": u, "cap": 0.0, "cost": -cost, "flow": 0.0, "rev": len(edges), "id": edge_id, "forward": False}
            adjacency.setdefault(u, []).append(len(edges))
            edges.append(forward)
            adjacency.setdefault(v, []).append(len(edges))
            edges.append(reverse)

        for edge in graph.edges:
            capacity = float(edge.metadata.get("capacity", edge.weight))
            cost = float(edge.metadata.get("cost", edge.label if edge.label not in (None, "") else 1))
            if capacity <= 0:
                continue
            add_edge(edge.source, edge.target, capacity, cost, edge.id or f"{edge.source}-{edge.target}")

        def display(value: float) -> int | float:
            return int(value) if value == int(value) else round(value, 2)

        def flow_table() -> list[dict]:
            rows = []
            for edge in edges:
                if not edge["forward"]:
                    continue
                rows.append(
                    {
                        "edge": f"{edge['u']}->{edge['v']}",
                        "flow": display(edge["flow"]),
                        "capacity": display(edge["cap"]),
                        "cost": display(edge["cost"]),
                        "residual": display(edge["cap"] - edge["flow"]),
                    }
                )
            return rows

        def shortest_path():
            dist = {node.id: float("inf") for node in graph.nodes}
            parent: dict[str, int] = {}
            in_queue = {node.id: False for node in graph.nodes}
            dist[source] = 0
            queue = deque([source])
            in_queue[source] = True
            scanned: list[dict] = []

            while queue:
                u = queue.popleft()
                in_queue[u] = False
                for edge_idx in adjacency.get(u, []):
                    edge = edges[edge_idx]
                    residual = edge["cap"] - edge["flow"]
                    if residual <= 0:
                        continue
                    v = edge["v"]
                    candidate = dist[u] + edge["cost"]
                    scanned.append({"from": u, "to": v, "residual": display(residual), "cost": display(edge["cost"])})
                    if candidate < dist.get(v, float("inf")):
                        dist[v] = candidate
                        parent[v] = edge_idx
                        if not in_queue.get(v, False):
                            queue.append(v)
                            in_queue[v] = True

            if sink not in parent:
                return [], 0.0, dist, scanned

            path = []
            bottleneck = float("inf")
            cursor = sink
            while cursor != source:
                edge_idx = parent[cursor]
                edge = edges[edge_idx]
                path.append(edge_idx)
                bottleneck = min(bottleneck, edge["cap"] - edge["flow"])
                cursor = edge["u"]
            path.reverse()
            return path, bottleneck, dist, scanned

        max_flow = 0.0
        min_cost = 0.0
        augmentations: list[dict] = []

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Start min-cost max-flow from {source} to {sink}",
            phase="init",
            state={"source": source, "sink": sink, "max_flow": 0, "min_cost": 0, "flow_table": flow_table()},
        )

        while True:
            path, bottleneck, dist, scanned = shortest_path()
            if not path:
                break

            path_nodes = [source] + [edges[idx]["v"] for idx in path]
            path_edges = [edges[idx]["id"] for idx in path if edges[idx]["forward"]]
            path_cost = sum(edges[idx]["cost"] for idx in path)

            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": path_nodes, "edges": path_edges},
                message=f"Shortest residual path {' -> '.join(path_nodes)} cost {display(path_cost)}, bottleneck {display(bottleneck)}",
                phase="explore",
                state={
                    "distances": {key: display(value) if value < float("inf") else "Infinity" for key, value in dist.items()},
                    "scanned_residual_edges": scanned,
                    "augmenting_path": path_nodes,
                    "path_cost": display(path_cost),
                    "bottleneck": display(bottleneck),
                    "flow_table": flow_table(),
                },
            )

            for edge_idx in path:
                edge = edges[edge_idx]
                rev = edges[edge["rev"]]
                edge["flow"] += bottleneck
                rev["flow"] -= bottleneck
            max_flow += bottleneck
            min_cost += bottleneck * path_cost
            augmentations.append({"path": path_nodes, "bottleneck": display(bottleneck), "path_cost": display(path_cost), "total_cost": display(min_cost)})

            for edge in edges:
                if not edge["forward"]:
                    continue
                yield Step(
                    action=StepAction.UPDATE_EDGE_LABEL,
                    target_type="edge",
                    target_id=edge["id"],
                    value=f"{edge['flow']:g}/{edge['cap']:g} c{edge['cost']:g}",
                    message=f"Flow {edge['u']} -> {edge['v']} is {edge['flow']:g}/{edge['cap']:g}, cost {edge['cost']:g}",
                    phase="relax",
                    state={"max_flow": display(max_flow), "min_cost": display(min_cost), "flow_table": flow_table(), "augmentations": list(augmentations)},
                )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Min-cost max-flow complete. Flow = {display(max_flow)}, cost = {display(min_cost)}",
            phase="result",
            state={"max_flow": display(max_flow), "min_cost": display(min_cost), "flow_table": flow_table(), "augmentations": augmentations},
        )

"""Push-relabel maximum flow visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class PushRelabelAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="push_relabel",
            category="graph",
            description="Maximum flow using preflow, node heights, push operations, and relabel operations",
            emoji="PR",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"},
                {"name": "target", "type": "str", "required": True, "description": "Sink node ID"},
            ],
            requires_weighted=True,
            requires_directed=True,
            allows_negative_weights=False,
            time_complexity="O(V^2E)",
            space_complexity="O(E)",
            use_cases=[
                "Dense maximum-flow networks",
                "Circulation and cut analysis",
                "Preflow-push education",
                "Network throughput optimization",
            ],
            pseudocode=(
                "height[source] = |V|\n"
                "saturate every edge leaving source to create a preflow\n"
                "while there is an active vertex u:\n"
                "    if admissible residual edge (u, v) exists:\n"
                "        push min(excess[u], residual(u, v))\n"
                "    else:\n"
                "        relabel u above its lowest residual neighbor\n"
                "return excess[sink]"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source")
        sink = params.get("target")
        if not source or not sink or source == sink:
            return

        node_ids = [node.id for node in graph.nodes]
        capacities: dict[tuple[str, str], float] = {}
        edge_ids: dict[tuple[str, str], str] = {}
        for edge in graph.edges:
            if edge.weight <= 0:
                continue
            key = (edge.source, edge.target)
            capacities[key] = capacities.get(key, 0.0) + float(edge.weight)
            edge_ids[key] = edge.id or f"{edge.source}-{edge.target}"

        flow = {key: 0.0 for key in capacities}
        height = {node_id: 0 for node_id in node_ids}
        excess = {node_id: 0.0 for node_id in node_ids}
        height[source] = len(node_ids)
        push_trace: list[dict] = []
        relabel_trace: list[dict] = []
        discharge_trace: list[dict] = []

        def display(value: float) -> int | float:
            return int(value) if value == int(value) else round(value, 2)

        def residual_from(node_id: str) -> list[tuple[str, tuple[str, str], str, float]]:
            rows = []
            for key, capacity in capacities.items():
                u, v = key
                current_flow = flow[key]
                if u == node_id and capacity - current_flow > 0:
                    rows.append((v, key, "forward", capacity - current_flow))
                if v == node_id and current_flow > 0:
                    rows.append((u, key, "reverse", current_flow))
            return rows

        def active_nodes() -> list[str]:
            return [
                node_id
                for node_id in node_ids
                if node_id not in {source, sink} and excess[node_id] > 0
            ]

        def flow_table() -> list[dict]:
            return [
                {
                    "edge": f"{u}->{v}",
                    "flow": display(flow[(u, v)]),
                    "capacity": display(capacity),
                    "residual": display(capacity - flow[(u, v)]),
                }
                for (u, v), capacity in capacities.items()
            ]

        def residual_network() -> list[dict]:
            rows = []
            for (u, v), capacity in capacities.items():
                current_flow = flow[(u, v)]
                forward = capacity - current_flow
                if forward > 0:
                    rows.append(
                        {
                            "from": u,
                            "to": v,
                            "direction": "forward",
                            "residual": display(forward),
                        }
                    )
                if current_flow > 0:
                    rows.append(
                        {
                            "from": v,
                            "to": u,
                            "direction": "reverse",
                            "residual": display(current_flow),
                        }
                    )
            return rows

        def state(extra: dict | None = None) -> dict:
            payload = {
                "source": source,
                "sink": sink,
                "max_flow": display(excess[sink]),
                "heights": dict(height),
                "excess": {key: display(value) for key, value in excess.items()},
                "active_nodes": active_nodes(),
                "flow_table": flow_table(),
                "residual_network": residual_network(),
                "push_trace": list(push_trace),
                "relabel_trace": list(relabel_trace),
                "discharge_trace": list(discharge_trace),
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Initialize push-relabel: height[{source}] = {len(node_ids)}",
            phase="init",
            state=state(),
        )

        for key, capacity in list(capacities.items()):
            u, v = key
            if u != source or capacity <= 0:
                continue
            flow[key] = capacity
            excess[source] -= capacity
            excess[v] += capacity
            event = {
                "from": u,
                "to": v,
                "edge": f"{u}->{v}",
                "amount": display(capacity),
                "type": "initial preflow",
            }
            push_trace.append(event)
            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge_ids[key],
                value="current",
                message=f"Saturate source edge {u} -> {v} with {display(capacity)} units of preflow",
                phase="init",
                state=state({"current_push": event}),
            )
            yield Step(
                action=StepAction.UPDATE_EDGE_LABEL,
                target_type="edge",
                target_id=edge_ids[key],
                value=f"{flow[key]:g}/{capacity:g}",
                message="",
                phase="init",
                state=state({"current_push": event}),
            )

        while True:
            queue = active_nodes()
            if not queue:
                break
            node_id = queue[0]
            discharge = {"node": node_id, "start_excess": display(excess[node_id]), "pushes": 0, "relabels": 0}
            discharge_trace.append(discharge)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="current",
                message=f"Discharge active node {node_id} with excess {display(excess[node_id])}",
                phase="explore",
                state=state({"current_discharge": discharge}),
            )

            while excess[node_id] > 0:
                admissible = [
                    item for item in residual_from(node_id)
                    if item[3] > 0 and height[node_id] == height[item[0]] + 1
                ]
                if not admissible:
                    residual_neighbors = [item for item in residual_from(node_id) if item[3] > 0]
                    if not residual_neighbors:
                        break
                    old_height = height[node_id]
                    height[node_id] = min(height[neighbor] for neighbor, _, _, _ in residual_neighbors) + 1
                    event = {
                        "node": node_id,
                        "from": old_height,
                        "to": height[node_id],
                        "residual_neighbors": [
                            {"node": neighbor, "height": height[neighbor], "residual": display(residual)}
                            for neighbor, _, _, residual in residual_neighbors
                        ],
                    }
                    relabel_trace.append(event)
                    discharge["relabels"] += 1
                    yield Step(
                        action=StepAction.UPDATE_NODE_LABEL,
                        target_type="node",
                        target_id=node_id,
                        value=f"{node_id}\nh={height[node_id]}\ne={display(excess[node_id])}",
                        message=f"Relabel {node_id}: {old_height} -> {height[node_id]}",
                        phase="relax",
                        state=state({"current_relabel": event, "current_discharge": discharge}),
                    )
                    continue

                neighbor, key, direction, residual = admissible[0]
                amount = min(excess[node_id], residual)
                if direction == "forward":
                    flow[key] += amount
                    start, end = key
                else:
                    flow[key] -= amount
                    end, start = key
                excess[node_id] -= amount
                excess[neighbor] += amount

                event = {
                    "from": node_id,
                    "to": neighbor,
                    "edge": f"{key[0]}->{key[1]}",
                    "direction": direction,
                    "amount": display(amount),
                    "remaining_excess": display(excess[node_id]),
                }
                push_trace.append(event)
                discharge["pushes"] += 1

                yield Step(
                    action=StepAction.MARK_PATH,
                    target_type="node",
                    target_id="",
                    value={"nodes": [node_id, neighbor], "edges": [edge_ids[key]]},
                    message=f"Push {display(amount)} from {node_id} to {neighbor} on {direction} residual edge",
                    phase="relax",
                    state=state({"current_push": event, "current_discharge": discharge}),
                )
                yield Step(
                    action=StepAction.UPDATE_EDGE_LABEL,
                    target_type="edge",
                    target_id=edge_ids[key],
                    value=f"{flow[key]:g}/{capacities[key]:g}",
                    message=f"Flow on {start} -> {end} is now {flow[key]:g}/{capacities[key]:g}",
                    phase="relax",
                    state=state({"current_push": event, "current_discharge": discharge}),
                )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Push-relabel complete. Max flow = {display(excess[sink])}",
            phase="result",
            state=state(),
        )

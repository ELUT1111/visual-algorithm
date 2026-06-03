"""Bridge, articulation point, and biconnected component detection."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BridgesArticulationAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="bridges_articulation",
            category="graph",
            description="Find bridges, articulation points, and edge-biconnected components with DFS low-link values",
            emoji="LL",
            parameters=[],
            requires_undirected=True,
            time_complexity="O(V + E)",
            space_complexity="O(V + E)",
            use_cases=[
                "Network reliability analysis",
                "Critical road or cable detection",
                "Biconnected component decomposition",
                "Finding single points of failure",
            ],
            pseudocode=(
                "DFS(u):\n"
                "    disc[u] = low[u] = timer++\n"
                "    for each edge u-v:\n"
                "        if v unvisited:\n"
                "            push edge on stack; DFS(v)\n"
                "            low[u] = min(low[u], low[v])\n"
                "            if low[v] > disc[u]: edge u-v is a bridge\n"
                "            if low[v] >= disc[u]: pop one biconnected component\n"
                "        else if v is not parent and disc[v] < disc[u]:\n"
                "            push back edge; low[u] = min(low[u], disc[v])"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        adjacency: dict[str, list[tuple[str, str]]] = {node.id: [] for node in graph.nodes}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            adjacency.setdefault(edge.target, []).append((edge.source, edge_id))

        timer = 0
        disc: dict[str, int] = {}
        low: dict[str, int] = {}
        parent: dict[str, str | None] = {node.id: None for node in graph.nodes}
        bridges: list[dict[str, str]] = []
        articulation: set[str] = set()
        dfs_stack: list[str] = []
        edge_stack: list[dict[str, str]] = []
        biconnected_components: list[dict] = []
        component_trace: list[dict] = []

        def state(extra: dict | None = None) -> dict:
            payload = {
                "stack": list(dfs_stack),
                "edge_stack": list(edge_stack),
                "disc": dict(disc),
                "low": dict(low),
                "parent": {node: pred for node, pred in parent.items() if pred is not None},
                "bridges": list(bridges),
                "articulation_points": sorted(articulation),
                "biconnected_components": list(biconnected_components),
                "component_trace": list(component_trace),
            }
            if extra:
                payload.update(extra)
            return payload

        def pop_component(stop_edge_id: str, reason: str) -> dict:
            component_edges: list[dict[str, str]] = []
            component_nodes: set[str] = set()
            while edge_stack:
                item = edge_stack.pop()
                component_edges.append(item)
                component_nodes.add(item["from"])
                component_nodes.add(item["to"])
                if item["edge"] == stop_edge_id:
                    break
            component = {
                "id": len(biconnected_components) + 1,
                "reason": reason,
                "edges": list(reversed(component_edges)),
                "nodes": sorted(component_nodes),
            }
            biconnected_components.append(component)
            component_trace.append(component)
            return component

        def dfs(node_id: str, root: str) -> Generator[Step, None, None]:
            nonlocal timer
            disc[node_id] = timer
            low[node_id] = timer
            timer += 1
            child_count = 0
            dfs_stack.append(node_id)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="current",
                message=f"Visit {node_id}: disc={disc[node_id]}, low={low[node_id]}",
                phase="explore",
                state=state({"current": node_id}),
            )

            for neighbor, edge_id in adjacency.get(node_id, []):
                if neighbor == parent[node_id]:
                    continue

                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Inspect edge {node_id} -- {neighbor}",
                    phase="explore",
                    state=state({"current_edge": edge_id}),
                )

                if neighbor not in disc:
                    parent[neighbor] = node_id
                    child_count += 1
                    edge_item = {"edge": edge_id, "from": node_id, "to": neighbor, "type": "tree"}
                    edge_stack.append(edge_item)
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="edge",
                        target_id=edge_id,
                        message=f"Push tree edge {node_id} -- {neighbor} onto BCC edge stack",
                        phase="explore",
                        state=state({"pushed_edge": edge_item}),
                    )

                    yield from dfs(neighbor, root)

                    low[node_id] = min(low[node_id], low[neighbor])
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="node",
                        target_id=node_id,
                        message=f"After {neighbor}, low[{node_id}] = {low[node_id]}",
                        phase="relax",
                        state=state({"current": node_id, "child": neighbor}),
                    )

                    if low[neighbor] > disc[node_id]:
                        bridges.append({"edge": edge_id, "from": node_id, "to": neighbor})
                        yield Step(
                            action=StepAction.SET_EDGE_COLOR,
                            target_type="edge",
                            target_id=edge_id,
                            value="path",
                            message=f"Bridge found: {node_id} -- {neighbor}",
                            phase="result",
                            state=state({"bridge": edge_id}),
                        )

                    if (node_id == root and child_count > 1) or (
                        node_id != root and low[neighbor] >= disc[node_id]
                    ):
                        articulation.add(node_id)
                        yield Step(
                            action=StepAction.SET_NODE_COLOR,
                            target_type="node",
                            target_id=node_id,
                            value="path",
                            message=f"Articulation point found: {node_id}",
                            phase="result",
                            state=state({"articulation": node_id}),
                        )

                    if low[neighbor] >= disc[node_id]:
                        component = pop_component(edge_id, f"low[{neighbor}] >= disc[{node_id}]")
                        yield Step(
                            action=StepAction.MARK_PATH,
                            target_type="node",
                            target_id="",
                            value={"nodes": component["nodes"], "edges": [edge["edge"] for edge in component["edges"]]},
                            message=f"Biconnected component {component['id']}: {', '.join(component['nodes'])}",
                            phase="result",
                            state=state({"biconnected_component": component}),
                        )
                elif disc[neighbor] < disc[node_id]:
                    edge_item = {"edge": edge_id, "from": node_id, "to": neighbor, "type": "back"}
                    edge_stack.append(edge_item)
                    low[node_id] = min(low[node_id], disc[neighbor])
                    yield Step(
                        action=StepAction.ADD_MESSAGE,
                        target_type="edge",
                        target_id=edge_id,
                        message=f"Back edge to {neighbor}; push edge and set low[{node_id}] = {low[node_id]}",
                        phase="relax",
                        state=state({"back_edge": edge_item}),
                    )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="explore",
                    state=state(),
                )

            dfs_stack.pop()
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="visited",
                message=f"Finish {node_id}",
                phase="finalize",
                state=state({"current": node_id}),
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Start DFS low-link scan with BCC edge stack",
            phase="init",
            state=state(),
        )

        for node in graph.nodes:
            if node.id not in disc:
                yield from dfs(node.id, node.id)
                if edge_stack:
                    component = pop_component(edge_stack[-1]["edge"], "flush remaining component after DFS root")
                    yield Step(
                        action=StepAction.MARK_PATH,
                        target_type="node",
                        target_id="",
                        value={"nodes": component["nodes"], "edges": [edge["edge"] for edge in component["edges"]]},
                        message=f"Biconnected component {component['id']}: {', '.join(component['nodes'])}",
                        phase="result",
                        state=state({"biconnected_component": component}),
                    )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=(
                f"Found {len(bridges)} bridge(s), {len(articulation)} articulation point(s), "
                f"and {len(biconnected_components)} biconnected component(s)"
            ),
            phase="result",
            state=state(),
        )

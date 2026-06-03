"""Chu-Liu/Edmonds minimum directed spanning tree algorithm."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class DirectedMSTAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="directed_mst",
            category="graph",
            description="Find a minimum-cost rooted arborescence in a directed graph with Chu-Liu/Edmonds",
            emoji="DMST",
            parameters=[
                {
                    "name": "source",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "Root node ID; defaults to graph root or the first node",
                }
            ],
            requires_weighted=True,
            requires_directed=True,
            time_complexity="O(V * E)",
            space_complexity="O(V + E)",
            use_cases=[
                "Directed network design",
                "Broadcast tree optimization",
                "Dependency arborescence extraction",
                "Rooted routing and control-plane planning",
            ],
            pseudocode=(
                "for every vertex except root, choose the cheapest incoming edge\n"
                "if the chosen edges contain no directed cycle: return them\n"
                "contract one chosen-edge cycle into a supernode\n"
                "subtract each cycle vertex incoming cost from edges entering the cycle\n"
                "solve the contracted graph recursively\n"
                "expand the cycle and replace one cycle edge with the entering edge"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        root = str(params.get("source", "") or "").strip() or graph.root_id or node_ids[0]
        if root not in node_ids:
            root = node_ids[0]

        adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        original_edges: list[dict] = []
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append(edge.target)
            original_edges.append(
                {
                    "id": edge_id,
                    "source": edge.source,
                    "target": edge.target,
                    "weight": float(edge.weight),
                    "base": None,
                }
            )

        reachable = []
        seen = {root}
        queue = deque([root])
        while queue:
            current = queue.popleft()
            reachable.append(current)
            for neighbor in adjacency.get(current, []):
                if neighbor in seen or neighbor not in node_ids:
                    continue
                seen.add(neighbor)
                queue.append(neighbor)

        unreachable = [node_id for node_id in node_ids if node_id not in seen]

        def display(value: float):
            return int(value) if value.is_integer() else round(value, 3)

        def edge_row(edge: dict, *, adjusted: bool = False) -> dict:
            weight_key = "adjusted_weight" if adjusted else "weight"
            return {
                "edge": edge["id"],
                "source": edge["source"],
                "target": edge["target"],
                weight_key: display(float(edge["weight"])),
            }

        def state(extra: dict | None = None) -> dict:
            payload = {
                "root": root,
                "reachable_nodes": list(reachable),
                "unreachable_nodes": list(unreachable),
                "selected_incoming": [],
                "cycle_trace": [],
                "contractions": [],
                "arborescence_edges": [],
                "total_weight": 0,
            }
            if extra:
                payload.update(extra)
            return payload

        if unreachable:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id=root,
                message=f"Cannot build directed MST: unreachable nodes from {root}: {', '.join(unreachable)}",
                phase="result",
                state=state(),
            )
            return

        selected_rounds: list[dict] = []
        cycle_trace: list[dict] = []
        contractions: list[dict] = []
        supernode_count = 0

        def find_cycle(nodes: list[str], current_root: str, min_incoming: dict[str, dict]) -> list[str] | None:
            for start in nodes:
                path: list[str] = []
                position: dict[str, int] = {}
                current = start
                while current != current_root and current in min_incoming:
                    if current in position:
                        return path[position[current]:]
                    position[current] = len(path)
                    path.append(current)
                    current = min_incoming[current]["source"]
            return None

        def edmonds(nodes: list[str], current_root: str, edges: list[dict], level: int) -> list[dict]:
            nonlocal supernode_count

            min_incoming: dict[str, dict] = {}
            round_rows = []
            for node_id in nodes:
                if node_id == current_root:
                    continue
                incoming = [
                    edge for edge in edges
                    if edge["target"] == node_id and edge["source"] != node_id
                ]
                if not incoming:
                    raise ValueError(f"No incoming edge can reach {node_id}")
                chosen = min(incoming, key=lambda edge: (edge["weight"], edge["id"]))
                min_incoming[node_id] = chosen
                round_rows.append(edge_row(chosen, adjusted=bool(chosen.get("adjusted"))))

            selected_rounds.append(
                {
                    "level": level,
                    "root": current_root,
                    "nodes": list(nodes),
                    "selected_edges": round_rows,
                }
            )

            cycle = find_cycle(nodes, current_root, min_incoming)
            if not cycle:
                return list(min_incoming.values())

            cycle_set = set(cycle)
            cycle_edges = [min_incoming[node_id] for node_id in cycle]
            supernode_count += 1
            supernode = f"cycle_{supernode_count}"

            cycle_trace.append(
                {
                    "level": level,
                    "cycle": list(cycle),
                    "cycle_edges": [edge_row(edge) for edge in cycle_edges],
                    "contracted_as": supernode,
                }
            )

            next_nodes = [node_id for node_id in nodes if node_id not in cycle_set] + [supernode]
            next_edges = []
            adjusted_rows = []
            for edge in edges:
                source_in = edge["source"] in cycle_set
                target_in = edge["target"] in cycle_set
                if source_in and target_in:
                    continue
                if not source_in and target_in:
                    entering_vertex = edge["target"]
                    adjusted_weight = edge["weight"] - min_incoming[entering_vertex]["weight"]
                    contracted = {
                        **edge,
                        "source": edge["source"],
                        "target": supernode,
                        "weight": adjusted_weight,
                        "base": edge,
                        "enter": entering_vertex,
                        "adjusted": True,
                    }
                    next_edges.append(contracted)
                    adjusted_rows.append(
                        {
                            **edge_row(contracted, adjusted=True),
                            "original_target": entering_vertex,
                            "subtract": display(float(min_incoming[entering_vertex]["weight"])),
                        }
                    )
                elif source_in and not target_in:
                    next_edges.append(
                        {
                            **edge,
                            "source": supernode,
                            "target": edge["target"],
                            "base": edge,
                            "exit": edge["source"],
                        }
                    )
                else:
                    next_edges.append({**edge, "base": edge})

            contractions.append(
                {
                    "level": level,
                    "cycle": list(cycle),
                    "supernode": supernode,
                    "adjusted_entering_edges": adjusted_rows,
                }
            )

            contracted_result = edmonds(next_nodes, current_root, next_edges, level + 1)
            expanded: list[dict] = []
            removed_cycle_vertex = None
            for edge in contracted_result:
                base = edge.get("base") or edge
                if edge["target"] == supernode:
                    removed_cycle_vertex = edge.get("enter")
                    expanded.append(base)
                elif edge["source"] == supernode:
                    expanded.append(base)
                else:
                    expanded.append(base)

            for node_id in cycle:
                if node_id != removed_cycle_vertex:
                    expanded.append(min_incoming[node_id])

            return expanded

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id=root,
            message=f"Start directed MST from root {root}",
            phase="init",
            state=state(),
        )

        try:
            result_edges = edmonds(list(node_ids), root, original_edges, 0)
        except ValueError as exc:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id=root,
                message=f"Cannot build directed MST: {exc}",
                phase="result",
                state=state(
                    {
                        "selected_incoming": selected_rounds,
                        "cycle_trace": cycle_trace,
                        "contractions": contractions,
                    }
                ),
            )
            return

        unique_result = []
        seen_edges = set()
        for edge in result_edges:
            if edge["id"] in seen_edges:
                continue
            seen_edges.add(edge["id"])
            unique_result.append(edge)

        arborescence_edges = [edge_row(edge) for edge in unique_result]
        total_weight = sum(float(edge["weight"]) for edge in unique_result)
        final_state = state(
            {
                "selected_incoming": selected_rounds,
                "cycle_trace": cycle_trace,
                "contractions": contractions,
                "arborescence_edges": arborescence_edges,
                "total_weight": display(total_weight),
            }
        )

        for round_info in selected_rounds:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Level {round_info['level']}: choose cheapest incoming edge for each non-root node",
                phase="explore",
                state=state(
                    {
                        "selected_incoming": selected_rounds[: round_info["level"] + 1],
                        "cycle_trace": cycle_trace,
                        "contractions": contractions,
                    }
                ),
            )

        for trace in cycle_trace:
            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": trace["cycle"], "edges": [edge["edge"] for edge in trace["cycle_edges"]]},
                message=f"Contract directed cycle {' -> '.join(trace['cycle'])} as {trace['contracted_as']}",
                phase="relax",
                state=state(
                    {
                        "selected_incoming": selected_rounds,
                        "cycle_trace": cycle_trace,
                        "contractions": contractions,
                    }
                ),
            )

        for edge in unique_result:
            yield Step(
                action=StepAction.HIGHLIGHT_EDGE,
                target_type="edge",
                target_id=edge["id"],
                value="mst",
                message=f"Arborescence edge {edge['source']} -> {edge['target']} (weight={display(float(edge['weight']))})",
                phase="result",
                state=final_state,
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Directed MST complete: total weight {display(total_weight)}, edges {len(unique_result)}",
            phase="result",
            state=final_state,
        )

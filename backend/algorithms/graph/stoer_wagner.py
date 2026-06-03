"""Stoer-Wagner global minimum cut algorithm."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class StoerWagnerAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="stoer_wagner",
            category="graph",
            description="Find the global minimum cut in an undirected weighted graph by repeated vertex contraction",
            emoji="CUT",
            parameters=[],
            requires_weighted=True,
            requires_undirected=True,
            allows_negative_weights=False,
            time_complexity="O(V^3)",
            space_complexity="O(V^2)",
            use_cases=[
                "Network reliability bottlenecks",
                "Graph partitioning",
                "Clustering by sparse cuts",
                "Circuit and infrastructure vulnerability analysis",
            ],
            pseudocode=(
                "best_cut = infinity\n"
                "while more than one supernode remains:\n"
                "    A = []\n"
                "    repeatedly add the vertex most tightly connected to A\n"
                "    let s and t be the last two added vertices\n"
                "    cut_weight = connection_weight(t, A - {t})\n"
                "    best_cut = min(best_cut, cut_weight)\n"
                "    contract s and t\n"
                "return best_cut"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if len(node_ids) < 2:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="Stoer-Wagner needs at least two nodes",
                phase="result",
                state={"best_cut_value": 0, "best_cut": node_ids, "min_cut_edges": []},
            )
            return

        adjacency: dict[str, dict[str, float]] = {node_id: {} for node_id in node_ids}
        original_edges: list[dict] = []

        for edge in graph.edges:
            if edge.source == edge.target:
                continue
            weight = float(edge.weight)
            adjacency.setdefault(edge.source, {})
            adjacency.setdefault(edge.target, {})
            adjacency[edge.source][edge.target] = adjacency[edge.source].get(edge.target, 0.0) + weight
            adjacency[edge.target][edge.source] = adjacency[edge.target].get(edge.source, 0.0) + weight
            original_edges.append(
                {
                    "id": edge.id or f"{edge.source}-{edge.target}",
                    "source": edge.source,
                    "target": edge.target,
                    "weight": weight,
                }
            )

        def display(value):
            if value == float("inf"):
                return "Infinity"
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return round(value, 3) if isinstance(value, float) else value

        active = list(node_ids)
        groups: dict[str, set[str]] = {node_id: {node_id} for node_id in node_ids}
        best_cut_value = float("inf")
        best_cut: list[str] = []
        best_cut_edges: list[dict] = []
        contractions: list[dict] = []
        phase_cuts: list[dict] = []

        def cut_edges(cut_nodes: set[str]) -> list[dict]:
            rows = []
            for edge in original_edges:
                source_in = edge["source"] in cut_nodes
                target_in = edge["target"] in cut_nodes
                if source_in != target_in:
                    rows.append(
                        {
                            "edge": edge["id"],
                            "source": edge["source"],
                            "target": edge["target"],
                            "weight": display(edge["weight"]),
                        }
                    )
            return rows

        def state(extra: dict | None = None) -> dict:
            payload = {
                "active_supernodes": list(active),
                "supernodes": {key: sorted(value) for key, value in groups.items() if key in active},
                "best_cut_value": display(best_cut_value),
                "best_cut": list(best_cut),
                "min_cut_edges": list(best_cut_edges),
                "phase_cuts": list(phase_cuts),
                "contractions": list(contractions),
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Start Stoer-Wagner global min-cut with {len(active)} nodes",
            phase="init",
            state=state(),
        )

        phase_number = 1
        while len(active) > 1:
            selected: list[str] = []
            connection_weights = {node_id: 0.0 for node_id in active}
            phase_order: list[dict] = []

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Phase {phase_number}: grow a maximum-adjacency set",
                phase="explore",
                state=state({"phase": phase_number, "phase_order": [], "connection_weights": {key: 0 for key in active}}),
            )

            for index in range(len(active)):
                remaining = [node_id for node_id in active if node_id not in selected]
                chosen = max(remaining, key=lambda node_id: (connection_weights[node_id], node_id))
                chosen_weight = connection_weights[chosen]
                selected.append(chosen)
                phase_order.append(
                    {
                        "step": index + 1,
                        "supernode": chosen,
                        "members": sorted(groups[chosen]),
                        "connection_weight": display(chosen_weight),
                    }
                )

                yield Step(
                    action=StepAction.MARK_PATH,
                    target_type="node",
                    target_id="",
                    value={"nodes": sorted(groups[chosen]), "edges": []},
                    message=f"Phase {phase_number}: add supernode {chosen} with connection weight {display(chosen_weight)}",
                    phase="explore",
                    state=state(
                        {
                            "phase": phase_number,
                            "selected_supernodes": list(selected),
                            "phase_order": list(phase_order),
                            "connection_weights": {key: display(value) for key, value in connection_weights.items() if key in active},
                        }
                    ),
                )

                if index == len(active) - 1:
                    break

                for neighbor, weight in adjacency.get(chosen, {}).items():
                    if neighbor in active and neighbor not in selected:
                        connection_weights[neighbor] += weight

            source_supernode = selected[-2]
            sink_supernode = selected[-1]
            cut_nodes = set(groups[sink_supernode])
            current_cut_edges = cut_edges(cut_nodes)
            current_cut_value = sum(float(edge["weight"]) for edge in current_cut_edges)
            if abs(current_cut_value - connection_weights[sink_supernode]) < 1e-9:
                current_cut_value = connection_weights[sink_supernode]

            cut_record = {
                "phase": phase_number,
                "cut_value": display(current_cut_value),
                "cut": sorted(cut_nodes),
                "last_two": [source_supernode, sink_supernode],
            }
            phase_cuts.append(cut_record)

            if current_cut_value < best_cut_value:
                best_cut_value = current_cut_value
                best_cut = sorted(cut_nodes)
                best_cut_edges = current_cut_edges
                best_message = "new best"
            else:
                best_message = "kept previous best"

            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": sorted(cut_nodes), "edges": [edge["edge"] for edge in current_cut_edges]},
                message=(
                    f"Phase {phase_number}: cut around {sink_supernode} has value "
                    f"{display(current_cut_value)} ({best_message})"
                ),
                phase="finalize",
                state=state(
                    {
                        "phase": phase_number,
                        "phase_order": list(phase_order),
                        "current_cut": cut_record,
                        "current_cut_edges": current_cut_edges,
                    }
                ),
            )

            contraction = {
                "phase": phase_number,
                "kept": source_supernode,
                "merged": sink_supernode,
                "members": sorted(groups[source_supernode] | groups[sink_supernode]),
            }
            contractions.append(contraction)

            groups[source_supernode].update(groups[sink_supernode])
            del groups[sink_supernode]

            for neighbor in list(active):
                if neighbor in (source_supernode, sink_supernode):
                    continue
                merged_weight = adjacency.get(source_supernode, {}).get(neighbor, 0.0) + adjacency.get(sink_supernode, {}).get(neighbor, 0.0)
                if merged_weight:
                    adjacency[source_supernode][neighbor] = merged_weight
                    adjacency[neighbor][source_supernode] = merged_weight
                adjacency[neighbor].pop(sink_supernode, None)

            adjacency[source_supernode].pop(sink_supernode, None)
            adjacency.pop(sink_supernode, None)
            active.remove(sink_supernode)

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Contract {sink_supernode} into {source_supernode}",
                phase="relax",
                state=state({"phase": phase_number, "last_contraction": contraction}),
            )

            phase_number += 1

        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": best_cut, "edges": [edge["edge"] for edge in best_cut_edges]},
            message=f"Stoer-Wagner complete: global min cut value {display(best_cut_value)}",
            phase="result",
            state=state(),
        )

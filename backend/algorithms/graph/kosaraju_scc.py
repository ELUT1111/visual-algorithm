"""Kosaraju strongly connected components visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class KosarajuSCCAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="kosaraju_scc",
            category="graph",
            description="Find strongly connected components with two DFS passes",
            emoji="🔁",
            parameters=[],
            requires_directed=True,
            time_complexity="O(V + E)",
            space_complexity="O(V + E)",
            use_cases=[
                "Strongly connected component decomposition",
                "Directed graph condensation",
                "Dependency cycle analysis",
                "Alternative to Tarjan SCC",
            ],
            pseudocode=(
                "function Kosaraju(graph):\n"
                "    run DFS and push vertices by finish time\n"
                "    reverse every edge\n"
                "    run DFS in reverse finish order\n"
                "    each reverse DFS tree is one SCC"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        reverse: dict[str, list[str]] = {node_id: [] for node_id in node_ids}

        for edge in graph.edges:
            if edge.source in adjacency and edge.target in adjacency:
                adjacency[edge.source].append(edge.target)
                reverse[edge.target].append(edge.source)

        visited: set[str] = set()
        finish_order: list[str] = []

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Start first DFS pass to compute finish order",
            phase="init",
            state={"finish_order": [], "visited": []},
        )

        def first_pass(node_id: str) -> Generator[Step, None, None]:
            visited.add(node_id)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="current",
                message=f"First pass visits {node_id}",
                phase="explore",
                state={"finish_order": list(finish_order), "visited": sorted(visited)},
            )

            for neighbor in adjacency.get(node_id, []):
                if neighbor not in visited:
                    yield from first_pass(neighbor)

            finish_order.append(node_id)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="visited",
                message=f"Finish {node_id}; push to order",
                phase="finalize",
                state={"finish_order": list(finish_order), "visited": sorted(visited)},
            )

        for node_id in node_ids:
            if node_id not in visited:
                yield from first_pass(node_id)

        components: list[list[str]] = []
        assigned: set[str] = set()

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Run second DFS pass on the reversed graph",
            phase="init",
            state={"finish_order": list(finish_order), "components": []},
        )

        def second_pass(node_id: str, component: list[str]) -> Generator[Step, None, None]:
            assigned.add(node_id)
            component.append(node_id)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="current",
                message=f"Reverse pass adds {node_id} to current SCC",
                phase="explore",
                state={
                    "current_component": list(component),
                    "components": [list(c) for c in components],
                    "assigned": sorted(assigned),
                },
            )

            for neighbor in reverse.get(node_id, []):
                if neighbor not in assigned:
                    yield from second_pass(neighbor, component)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="visited",
                message=f"Finalize {node_id} in current SCC",
                phase="finalize",
                state={
                    "current_component": list(component),
                    "components": [list(c) for c in components],
                    "assigned": sorted(assigned),
                },
            )

        for node_id in reversed(finish_order):
            if node_id in assigned:
                continue
            component: list[str] = []
            yield from second_pass(node_id, component)
            components.append(component)
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"SCC {len(components)}: {', '.join(component)}",
                phase="finalize",
                state={"components": [list(c) for c in components], "assigned": sorted(assigned)},
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Kosaraju complete. Found {len(components)} SCC(s)",
            phase="result",
            state={"components": [list(c) for c in components], "finish_order": list(finish_order)},
        )

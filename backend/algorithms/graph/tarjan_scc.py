"""Tarjan strongly connected components algorithm."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class TarjanSCCAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="tarjan_scc",
            category="graph",
            description="Find strongly connected components with Tarjan's algorithm",
            emoji="🧠",
            parameters=[],
            requires_directed=True,
            time_complexity="O(V + E)",
            space_complexity="O(V)",
            use_cases=[
                "Compiler dependency analysis",
                "Finding mutually reachable states",
                "Deadlock and cycle analysis",
                "Condensing directed graphs into DAGs",
            ],
            pseudocode=(
                "function TarjanSCC(graph):\n"
                "    index = 0\n"
                "    stack = empty\n"
                "    for each vertex v not visited:\n"
                "        strongconnect(v)\n"
                "\n"
                "function strongconnect(v):\n"
                "    index[v] = lowlink[v] = next index\n"
                "    push v onto stack\n"
                "    for each v -> w:\n"
                "        if w not visited: recurse and update lowlink[v]\n"
                "        else if w on stack: update lowlink[v]\n"
                "    if lowlink[v] == index[v]: pop one SCC"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        adjacency: dict[str, list[tuple[str, str]]] = {n.id: [] for n in graph.nodes}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))

        index_counter = 0
        indices: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        stack: list[str] = []
        on_stack: set[str] = set()
        components: list[list[str]] = []

        def state() -> dict:
            return {
                "stack": list(stack),
                "index": dict(indices),
                "lowlink": dict(lowlink),
                "components": [list(c) for c in components],
            }

        def strongconnect(node_id: str) -> Generator[Step, None, None]:
            nonlocal index_counter

            indices[node_id] = index_counter
            lowlink[node_id] = index_counter
            index_counter += 1
            stack.append(node_id)
            on_stack.add(node_id)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="current",
                message=f"Visit {node_id}: index={indices[node_id]}, lowlink={lowlink[node_id]}",
                phase="explore",
                state=state(),
            )

            for neighbor, edge_id in adjacency.get(node_id, []):
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Inspect edge {node_id} -> {neighbor}",
                    phase="explore",
                    state=state(),
                )

                if neighbor not in indices:
                    yield from strongconnect(neighbor)
                    old_lowlink = lowlink[node_id]
                    lowlink[node_id] = min(lowlink[node_id], lowlink[neighbor])
                    if lowlink[node_id] != old_lowlink:
                        yield Step(
                            action=StepAction.ADD_MESSAGE,
                            target_type="node",
                            target_id=node_id,
                            message=f"Update lowlink({node_id}) to {lowlink[node_id]} after returning from {neighbor}",
                            phase="relax",
                            state=state(),
                        )
                elif neighbor in on_stack:
                    old_lowlink = lowlink[node_id]
                    lowlink[node_id] = min(lowlink[node_id], indices[neighbor])
                    if lowlink[node_id] != old_lowlink:
                        yield Step(
                            action=StepAction.ADD_MESSAGE,
                            target_type="node",
                            target_id=node_id,
                            message=f"Back edge to stack node {neighbor}; lowlink({node_id}) = {lowlink[node_id]}",
                            phase="relax",
                            state=state(),
                        )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="explore",
                    state=state(),
                )

            if lowlink[node_id] == indices[node_id]:
                component: list[str] = []
                while stack:
                    popped = stack.pop()
                    on_stack.remove(popped)
                    component.append(popped)
                    if popped == node_id:
                        break
                component.reverse()
                components.append(component)

                yield Step(
                    action=StepAction.MARK_PATH,
                    target_type="node",
                    target_id="",
                    value=component,
                    message=f"SCC found: {', '.join(component)}",
                    phase="finalize",
                    state=state(),
                )
            else:
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=node_id,
                    value="visited",
                    message=f"Finished {node_id}; remains on stack",
                    phase="finalize",
                    state=state(),
                )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message="Start Tarjan SCC scan",
            phase="init",
            state=state(),
        )

        for node in graph.nodes:
            if node.id not in indices:
                yield from strongconnect(node.id)

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Found {len(components)} strongly connected component(s)",
            phase="result",
            state=state(),
        )

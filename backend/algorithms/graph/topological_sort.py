"""Topological sort for directed acyclic graphs."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class TopologicalSortAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="topological_sort",
            category="graph",
            description="Order DAG nodes so every edge points forward",
            emoji="📐",
            parameters=[],
            requires_directed=True,
            requires_dag=True,
            time_complexity="O(V + E)",
            space_complexity="O(V)",
            use_cases=[
                "Task scheduling with dependencies",
                "Build systems and package installation",
                "Course prerequisite ordering",
                "DAG pipeline planning",
            ],
            pseudocode=(
                "function TopologicalSort(graph):\n"
                "    indegree[v] = number of incoming edges\n"
                "    queue = all vertices with indegree 0\n"
                "    while queue is not empty:\n"
                "        u = queue.dequeue()\n"
                "        append u to order\n"
                "        for each edge u -> v:\n"
                "            indegree[v] -= 1\n"
                "            if indegree[v] == 0:\n"
                "                queue.enqueue(v)\n"
                "    return order"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        adjacency: dict[str, list[tuple[str, str]]] = {n.id: [] for n in graph.nodes}
        indegree: dict[str, int] = {n.id: 0 for n in graph.nodes}

        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            indegree[edge.target] = indegree.get(edge.target, 0) + 1

        queue = deque([node_id for node_id, degree in indegree.items() if degree == 0])
        order: list[str] = []

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Initial zero-indegree queue: {', '.join(queue) or '(empty)'}",
            phase="init",
            state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
        )

        for node_id, degree in indegree.items():
            yield Step(
                action=StepAction.UPDATE_NODE_LABEL,
                target_type="node",
                target_id=node_id,
                value=f"{node_id}\nin={degree}",
                message=f"Indegree({node_id}) = {degree}",
                phase="init",
                state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
            )

        while queue:
            current = queue.popleft()
            order.append(current)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Remove {current} from queue; append to topological order",
                phase="explore",
                state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
            )

            for neighbor, edge_id in adjacency.get(current, []):
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Process edge {current} -> {neighbor}",
                    phase="relax",
                    state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
                )

                indegree[neighbor] -= 1

                yield Step(
                    action=StepAction.UPDATE_NODE_LABEL,
                    target_type="node",
                    target_id=neighbor,
                    value=f"{neighbor}\nin={indegree[neighbor]}",
                    message=f"Decrement indegree({neighbor}) to {indegree[neighbor]}",
                    phase="relax",
                    state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
                )

                if indegree[neighbor] == 0:
                    queue.append(neighbor)
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=neighbor,
                        value="exploring",
                        message=f"{neighbor} now has indegree 0; enqueue it",
                        phase="relax",
                        state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
                    )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                    state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
                )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="visited",
                message=f"{current} finalized at position {len(order)}",
                phase="finalize",
                state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
            )

        if len(order) != len(graph.nodes):
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message="Cycle detected: no complete topological ordering exists",
                phase="result",
                state={"queue": list(queue), "indegree": dict(indegree), "order": list(order)},
            )
            return

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Topological order: {' -> '.join(order)}",
            phase="result",
            state={"queue": [], "indegree": dict(indegree), "order": list(order)},
        )

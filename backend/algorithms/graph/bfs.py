"""Breadth-First Search algorithm."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BFSAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="bfs",
            category="graph",
            description="Breadth-first search traversal from source",
            emoji="🔍",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"},
                {"name": "target", "type": "str", "required": False, "default": "", "description": "Target node (optional)"},
            ],
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source")
        target = params.get("target", "") or None
        if not source:
            source = graph.nodes[0].id if graph.nodes else None
        if not source:
            return

        # Build adjacency list
        adj: dict[str, list[str]] = {n.id: [] for n in graph.nodes}
        for e in graph.edges:
            adj.setdefault(e.source, []).append(e.target)
            if not graph.directed:
                adj.setdefault(e.target, []).append(e.source)

        visited = set([source])
        parent = {source: None}
        queue = deque([source])

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Starting BFS from node {source}",
            phase="init",
        )

        while queue:
            current = queue.popleft()

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Dequeued: {current}",
                phase="explore",
            )

            if target and current == target:
                # Trace path
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = parent.get(node)
                path.reverse()

                yield Step(
                    action=StepAction.MARK_PATH,
                    target_type="node",
                    target_id="",
                    value=path,
                    message=f"Found target {target}! Path: {' → '.join(path)}",
                    phase="result",
                )
                return

            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

                    # Find edge ID
                    edge_id = f"{current}-{neighbor}"
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        value="exploring",
                        message=f"Discovered {neighbor} via {current}",
                        phase="explore",
                    )

                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=neighbor,
                        value="exploring",
                        message=f"Enqueued: {neighbor}",
                        phase="explore",
                    )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="visited",
                message=f"Node {current} fully explored",
                phase="finalize",
            )

        if target:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Target {target} not reachable from {source}",
                phase="result",
            )
        else:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"BFS complete. Visited {len(visited)} nodes.",
                phase="result",
            )

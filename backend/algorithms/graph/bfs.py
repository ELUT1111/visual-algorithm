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
            time_complexity="O(V + E)",
            space_complexity="O(V)",
            use_cases=[
                "Shortest path in unweighted graphs",
                "Level-order tree traversal",
                "Web crawling / link discovery",
                "Finding connected components",
                "Social network degree of separation",
            ],
            pseudocode=(
                "function BFS(graph, source, target):\n"
                "    queue = [source]\n"
                "    visited = {source}\n"
                "    parent = {source: null}\n"
                "    while queue is not empty:\n"
                "        current = queue.dequeue()\n"
                "        if current == target:\n"
                "            return reconstruct_path(parent)\n"
                "        for each neighbor of current:\n"
                "            if neighbor not in visited:\n"
                "                visited.add(neighbor)\n"
                "                parent[neighbor] = current\n"
                "                queue.enqueue(neighbor)\n"
                "    return null  // target not reachable"
            ),
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

        def traversal_state(current: str | None = None) -> dict:
            return {
                "current": current,
                "target": target,
                "queue": list(queue),
                "visited": sorted(visited),
                "parent": {node: pred for node, pred in parent.items() if pred is not None},
            }

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Starting BFS from node {source}",
            phase="init",
            state=traversal_state(source),
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
                state=traversal_state(current),
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
                    state={**traversal_state(current), "path": path, "found": True},
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
                        state=traversal_state(current),
                    )

                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=neighbor,
                        value="exploring",
                        message=f"Enqueued: {neighbor}",
                        phase="explore",
                        state=traversal_state(current),
                    )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="visited",
                message=f"Node {current} fully explored",
                phase="finalize",
                state=traversal_state(current),
            )

        if target:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"Target {target} not reachable from {source}",
                phase="result",
                state={**traversal_state(), "found": False},
            )
        else:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"BFS complete. Visited {len(visited)} nodes.",
                phase="result",
                state=traversal_state(),
            )

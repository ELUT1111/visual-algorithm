"""Depth-First Search algorithm."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class DFSAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="dfs",
            category="graph",
            description="Depth-first search traversal from source",
            emoji="🔎",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Source node ID"},
                {"name": "target", "type": "str", "required": False, "default": "", "description": "Target node (optional)"},
            ],
            time_complexity="O(V + E)",
            space_complexity="O(V)",
            use_cases=[
                "Detecting cycles in graphs",
                "Topological sorting",
                "Finding connected components",
                "Solving mazes and puzzles",
                "Path finding in state-space graphs",
            ],
            pseudocode=(
                "function DFS(graph, source, target):\n"
                "    stack = [source]\n"
                "    visited = {source}\n"
                "    parent = {source: null}\n"
                "    while stack is not empty:\n"
                "        current = stack.pop()\n"
                "        if current == target:\n"
                "            return reconstruct_path(parent)\n"
                "        for each neighbor of current:\n"
                "            if neighbor not in visited:\n"
                "                visited.add(neighbor)\n"
                "                parent[neighbor] = current\n"
                "                stack.push(neighbor)\n"
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
        stack = [source]

        def traversal_state(current: str | None = None) -> dict:
            return {
                "current": current,
                "target": target,
                "stack": list(stack),
                "visited": sorted(visited),
                "parent": {node: pred for node, pred in parent.items() if pred is not None},
            }

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Starting DFS from node {source}",
            phase="init",
            state=traversal_state(source),
        )

        while stack:
            current = stack.pop()

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Popped: {current}",
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
                    message=f"Found target {target}! Path: {' -> '.join(path)}",
                    phase="result",
                    state={**traversal_state(current), "path": path, "found": True},
                )
                return

            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    stack.append(neighbor)

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
                        message=f"Pushed: {neighbor}",
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
                message=f"DFS complete. Visited {len(visited)} nodes.",
                phase="result",
                state=traversal_state(),
            )

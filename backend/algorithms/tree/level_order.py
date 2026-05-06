"""Level-order traversal with explicit level grouping."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class LevelOrderAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="level_order",
            category="tree",
            description="Level-order traversal showing nodes grouped by depth",
            emoji="📊",
            parameters=[
                {"name": "source", "type": "str", "required": False, "default": "",
                 "description": "Root node ID (uses graph.root_id if empty)"},
            ],
            time_complexity="O(n)",
            space_complexity="O(w) where w = max width",
            layout="hierarchical",
            use_cases=[
                "Level-by-level tree processing",
                "Finding level sums",
                "Right/left side view of tree",
                "Level order successor",
                "Cousins in binary tree",
            ],
            pseudocode=(
                "function LevelOrder(root):\n"
                "    queue = [root]\n"
                "    level = 0\n"
                "    while queue is not empty:\n"
                "        size = len(queue)\n"
                "        print 'Level ' + level\n"
                "        for i = 0 to size:\n"
                "            node = queue.dequeue()\n"
                "            visit(node)\n"
                "            for each child of node:\n"
                "                queue.enqueue(child)\n"
                "        level = level + 1"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        root = params.get("source") or graph.root_id
        if not root:
            root = graph.nodes[0].id if graph.nodes else None
        if not root:
            return

        # Build adjacency list (parent -> children)
        children: dict[str, list[str]] = {n.id: [] for n in graph.nodes}
        for e in graph.edges:
            children.setdefault(e.source, []).append(e.target)

        visited = set()
        queue = deque([root])
        level = 0

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=root,
            value="current",
            message=f"Starting level-order traversal from root {root}",
            phase="init",
        )

        while queue:
            level_size = len(queue)
            level_nodes = []

            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"--- Level {level} ---",
                phase="info",
            )

            for _ in range(level_size):
                current = queue.popleft()
                visited.add(current)
                level_nodes.append(current)

                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=current,
                    value="current",
                    message=f"Level {level}: visiting {current}",
                    phase="explore",
                )

                for child in children.get(current, []):
                    if child not in visited:
                        queue.append(child)

                        edge_id = f"{current}-{child}"
                        yield Step(
                            action=StepAction.HIGHLIGHT_EDGE,
                            target_type="edge",
                            target_id=edge_id,
                            value="exploring",
                            message=f"Edge {current} -> {child}",
                            phase="explore",
                        )

            # Mark all nodes at this level as visited
            for node_id in level_nodes:
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=node_id,
                    value="visited",
                    message=f"Level {level} complete: {', '.join(level_nodes)}",
                    phase="finalize",
                )

            level += 1

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Level-order complete. {level} levels, {len(visited)} nodes visited.",
            phase="result",
        )

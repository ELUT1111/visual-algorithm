"""Tree BFS (level-order traversal)."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class TreeBFSAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="tree_bfs",
            category="tree",
            description="Breadth-first search level-order traversal of a tree",
            emoji="🌊",
            parameters=[
                {"name": "source", "type": "str", "required": False, "default": "",
                 "description": "Root node ID (uses graph.root_id if empty)"},
            ],
            time_complexity="O(n)",
            space_complexity="O(w) where w = max width",
            layout="hierarchical",
            use_cases=[
                "Level-order traversal",
                "Finding shortest path in unweighted tree",
                "Printing tree level by level",
                "Finding minimum depth",
                "Zigzag traversal",
            ],
            pseudocode=(
                "function BFS_LevelOrder(root):\n"
                "    queue = [root]\n"
                "    while queue is not empty:\n"
                "        node = queue.dequeue()\n"
                "        visit(node)\n"
                "        for each child of node:\n"
                "            queue.enqueue(child)"
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

        visited = set([root])
        queue = deque([root])

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=root,
            value="current",
            message=f"Starting BFS from root {root}",
            phase="init",
        )

        while queue:
            current = queue.popleft()

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Processing {current}",
                phase="explore",
            )

            for child in children.get(current, []):
                if child not in visited:
                    visited.add(child)
                    queue.append(child)

                    edge_id = f"{current}-{child}"
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        value="exploring",
                        message=f"Discovered {child} from {current}",
                        phase="explore",
                    )
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=child,
                        value="exploring",
                        message=f"Enqueued {child}",
                        phase="explore",
                    )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="visited",
                message=f"Finished {current}",
                phase="finalize",
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"BFS complete. Visited {len(visited)} nodes.",
            phase="result",
        )

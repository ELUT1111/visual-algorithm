"""Tree DFS (preorder traversal)."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class TreeDFSAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="tree_dfs",
            category="tree",
            description="Depth-first search preorder traversal of a tree",
            emoji="🌲",
            parameters=[
                {"name": "source", "type": "str", "required": False, "default": "",
                 "description": "Root node ID (uses graph.root_id if empty)"},
            ],
            time_complexity="O(n)",
            space_complexity="O(h) where h = tree height",
            layout="hierarchical",
            use_cases=[
                "Preorder tree traversal",
                "Creating a copy of the tree",
                "Expression tree evaluation",
                "Serializing tree structure",
                "Finding tree depth",
            ],
            pseudocode=(
                "function DFS_Preorder(node):\n"
                "    if node is null:\n"
                "        return\n"
                "    visit(node)\n"
                "    for each child of node:\n"
                "        DFS_Preorder(child)"
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

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=root,
            value="current",
            message=f"Starting DFS from root {root}",
            phase="init",
        )

        def dfs(node_id: str):
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="current",
                message=f"Visiting {node_id}",
                phase="explore",
            )
            for child in children.get(node_id, []):
                edge_id = f"{node_id}-{child}"
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Traversing edge {node_id} -> {child}",
                    phase="explore",
                )
                yield from dfs(child)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_id,
                value="visited",
                message=f"Finished {node_id}",
                phase="finalize",
            )

        yield from dfs(root)

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"DFS complete. Visited {len(graph.nodes)} nodes.",
            phase="result",
        )

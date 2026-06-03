"""Lowest common ancestor with binary lifting."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class LCAAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="lca",
            category="tree",
            description="Find the lowest common ancestor of two tree nodes with binary lifting",
            emoji="LCA",
            parameters=[
                {
                    "name": "source",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "Root node ID (uses graph.root_id if empty)",
                },
                {"name": "node_a", "type": "str", "required": True, "description": "First query node ID"},
                {"name": "node_b", "type": "str", "required": True, "description": "Second query node ID"},
            ],
            time_complexity="Preprocess O(n log n), query O(log n)",
            space_complexity="O(n log n)",
            layout="hierarchical",
            use_cases=[
                "Tree ancestry queries",
                "Distance between two tree nodes",
                "Path queries in rooted trees",
                "Taxonomy and hierarchy navigation",
            ],
            pseudocode=(
                "root the tree and compute depth[v]\n"
                "up[v][0] = parent[v]\n"
                "for k from 1 to log n:\n"
                "    up[v][k] = up[up[v][k-1]][k-1]\n"
                "lift deeper query node until depths match\n"
                "lift both nodes together while ancestors differ\n"
                "return parent of either node"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        root = str(params.get("source", "") or graph.root_id or node_ids[0]).strip()
        node_a = str(params.get("node_a", "") or "").strip()
        node_b = str(params.get("node_b", "") or "").strip()

        adjacency: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in node_ids}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            adjacency.setdefault(edge.target, []).append((edge.source, edge_id))

        parent: dict[str, str | None] = {root: None}
        depth: dict[str, int] = {root: 0}
        parent_edge: dict[str, str] = {}
        traversal_order: list[str] = []

        def table_to_state(up: dict[str, list[str | None]] | None = None) -> dict[str, list[str]]:
            if not up:
                return {}
            return {node_id: [ancestor or "" for ancestor in ancestors] for node_id, ancestors in up.items()}

        def base_state(extra: dict | None = None) -> dict:
            payload = {
                "root": root,
                "node_a": node_a,
                "node_b": node_b,
                "parent": {node: pred for node, pred in parent.items() if pred is not None},
                "depth": dict(depth),
                "traversal_order": list(traversal_order),
            }
            if extra:
                payload.update(extra)
            return payload

        missing = [node_id for node_id in [root, node_a, node_b] if node_id not in node_ids]
        if missing:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"LCA cannot run: missing node(s) {', '.join(missing)}",
                phase="result",
                state=base_state({"lca": None, "error": "missing nodes"}),
            )
            return

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=root,
            value="current",
            message=f"Root tree at {root}; compute depth and parent links",
            phase="init",
            state=base_state(),
        )

        queue = deque([root])
        visited = {root}
        while queue:
            current = queue.popleft()
            traversal_order.append(current)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Visit {current} at depth {depth[current]}",
                phase="explore",
                state=base_state({"current": current}),
            )

            for neighbor, edge_id in adjacency.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                parent[neighbor] = current
                depth[neighbor] = depth[current] + 1
                parent_edge[neighbor] = edge_id
                queue.append(neighbor)
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Set parent({neighbor}) = {current}, depth = {depth[neighbor]}",
                    phase="explore",
                    state=base_state({"current": neighbor, "parent_edge": edge_id}),
                )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="visited",
                message=f"Finished preprocessing visit for {current}",
                phase="finalize",
                state=base_state({"current": current}),
            )

        if node_a not in visited or node_b not in visited:
            unreachable = [node_id for node_id in [node_a, node_b] if node_id not in visited]
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"LCA cannot run: query node(s) outside root component: {', '.join(unreachable)}",
                phase="result",
                state=base_state({"lca": None, "error": "disconnected query nodes"}),
            )
            return

        max_level = max(1, len(visited).bit_length())
        up: dict[str, list[str | None]] = {node_id: [None] * max_level for node_id in visited}
        for node_id in visited:
            up[node_id][0] = parent.get(node_id)
        for level in range(1, max_level):
            for node_id in visited:
                prev = up[node_id][level - 1]
                up[node_id][level] = up[prev][level - 1] if prev is not None else None

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Built binary lifting table with {max_level} level(s)",
            phase="init",
            state=base_state({"ancestor_table": table_to_state(up), "max_level": max_level}),
        )

        u = node_a
        v = node_b
        lift_trace: list[dict] = []

        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": [node_a, node_b], "edges": []},
            message=f"Query LCA({node_a}, {node_b})",
            phase="explore",
            state=base_state({
                "ancestor_table": table_to_state(up),
                "current_a": u,
                "current_b": v,
                "lift_trace": list(lift_trace),
            }),
        )

        if depth[u] < depth[v]:
            u, v = v, u

        diff = depth[u] - depth[v]
        for level in range(max_level - 1, -1, -1):
            if diff & (1 << level):
                before = u
                u = up[u][level]
                lift_trace.append({"node": before, "to": u, "level": level, "reason": "match depth"})
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=u or "",
                    value="current",
                    message=f"Lift {before} by 2^{level} to {u}",
                    phase="explore",
                    state=base_state({
                        "ancestor_table": table_to_state(up),
                        "current_a": u,
                        "current_b": v,
                        "lift_trace": list(lift_trace),
                    }),
                )
                if u is None:
                    break

        if u == v:
            lca = u
        else:
            for level in range(max_level - 1, -1, -1):
                if up[u][level] != up[v][level]:
                    before_u, before_v = u, v
                    u = up[u][level]
                    v = up[v][level]
                    lift_trace.append({"node_a": before_u, "to_a": u, "node_b": before_v, "to_b": v, "level": level})
                    yield Step(
                        action=StepAction.MARK_PATH,
                        target_type="node",
                        target_id="",
                        value={"nodes": [u, v], "edges": []},
                        message=f"Ancestors differ at 2^{level}; lift {before_u}->{u} and {before_v}->{v}",
                        phase="explore",
                        state=base_state({
                            "ancestor_table": table_to_state(up),
                            "current_a": u,
                            "current_b": v,
                            "lift_trace": list(lift_trace),
                        }),
                    )
            lca = parent.get(u)

        def path_to_root(node_id: str) -> list[str]:
            path: list[str] = []
            cursor: str | None = node_id
            while cursor is not None:
                path.append(cursor)
                cursor = parent.get(cursor)
            return path

        path_a = path_to_root(node_a)
        path_b = path_to_root(node_b)
        lca_path_nodes: list[str] = []
        if lca is not None:
            lca_path_nodes = path_a[: path_a.index(lca) + 1] + list(reversed(path_b[: path_b.index(lca)]))

        lca_path_edges: list[str] = []
        path_a_children = path_a[: path_a.index(lca)] if lca in path_a else []
        path_b_children = path_b[: path_b.index(lca)] if lca in path_b else []
        for child in path_a_children:
            lca_path_edges.append(parent_edge[child])
        for child in reversed(path_b_children):
            lca_path_edges.append(parent_edge[child])

        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": lca_path_nodes, "edges": lca_path_edges},
            message=f"LCA({node_a}, {node_b}) = {lca}",
            phase="result",
            state=base_state({
                "ancestor_table": table_to_state(up),
                "current_a": u,
                "current_b": v,
                "lca": lca,
                "path_a_to_root": path_a,
                "path_b_to_root": path_b,
                "lca_path": lca_path_nodes,
                "lca_path_edges": lca_path_edges,
                "lift_trace": lift_trace,
            }),
        )

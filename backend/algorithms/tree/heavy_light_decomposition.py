"""Heavy-Light Decomposition for tree path queries."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


def _parse_values(raw: str, node_ids: list[str]) -> dict[str, int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        return {node_id: 1 for node_id in node_ids}
    return {node_id: values[index] if index < len(values) else 1 for index, node_id in enumerate(node_ids)}


@registry.register
class HeavyLightDecompositionAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="heavy_light_decomposition",
            category="tree",
            description="Decompose a rooted tree into heavy paths for logarithmic path queries",
            emoji="HLD",
            parameters=[
                {"name": "source", "type": "str", "required": False, "default": "", "description": "Root node ID"},
                {"name": "node_a", "type": "str", "required": True, "description": "First path endpoint"},
                {"name": "node_b", "type": "str", "required": True, "description": "Second path endpoint"},
                {
                    "name": "values",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "Optional node values in graph node order",
                },
            ],
            time_complexity="Preprocess O(n), path query O(log n) segments",
            space_complexity="O(n)",
            layout="hierarchical",
            use_cases=[
                "Tree path sum queries",
                "Path maximum/minimum queries with a segment tree",
                "Dynamic tree analytics",
                "Competitive programming tree queries",
            ],
            pseudocode=(
                "dfs(root): compute parent, depth, subtree size, heavy child\n"
                "decompose(node, head):\n"
                "    assign head[node] and position[node]\n"
                "    continue through heavy child first\n"
                "    start new chains for light children\n"
                "query(u, v):\n"
                "    while head[u] != head[v]:\n"
                "        take deeper chain segment\n"
                "        move endpoint to parent[head]\n"
                "    take final same-chain segment"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        root = str(params.get("source", "") or graph.root_id or node_ids[0]).strip()
        node_a = str(params.get("node_a", "") or "").strip()
        node_b = str(params.get("node_b", "") or "").strip()
        try:
            node_values = _parse_values(str(params.get("values", "") or ""), node_ids)
        except ValueError:
            return

        adjacency: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in node_ids}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            adjacency.setdefault(edge.target, []).append((edge.source, edge_id))

        parent: dict[str, str | None] = {root: None}
        parent_edge: dict[str, str] = {}
        depth: dict[str, int] = {root: 0}
        subtree_size: dict[str, int] = {node_id: 1 for node_id in node_ids}
        heavy_child: dict[str, str | None] = {node_id: None for node_id in node_ids}
        head: dict[str, str] = {}
        position: dict[str, int] = {}
        base_array: list[int] = []
        chain_order: list[dict] = []
        dfs_order: list[str] = []
        decomposition_order: list[str] = []

        def base_state(extra: dict | None = None) -> dict:
            payload = {
                "root": root,
                "node_a": node_a,
                "node_b": node_b,
                "node_values": dict(node_values),
                "parent": {node: pred for node, pred in parent.items() if pred is not None},
                "depth": dict(depth),
                "subtree_size": dict(subtree_size),
                "heavy_child": {node: child for node, child in heavy_child.items() if child is not None},
                "head": dict(head),
                "position": dict(position),
                "base_array": list(base_array),
                "chain_order": list(chain_order),
                "dfs_order": list(dfs_order),
                "decomposition_order": list(decomposition_order),
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
                message=f"HLD cannot run: missing node(s) {', '.join(missing)}",
                phase="result",
                state=base_state({"error": "missing nodes"}),
            )
            return

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=root,
            value="current",
            message=f"Root tree at {root}; compute sizes and heavy children",
            phase="init",
            state=base_state({"current": root}),
        )

        stack = [root]
        visited = {root}
        while stack:
            current = stack.pop()
            dfs_order.append(current)
            for neighbor, edge_id in adjacency.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                parent[neighbor] = current
                parent_edge[neighbor] = edge_id
                depth[neighbor] = depth[current] + 1
                stack.append(neighbor)
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Set parent({neighbor}) = {current}, depth = {depth[neighbor]}",
                    phase="explore",
                    state=base_state({"current": neighbor}),
                )

        if node_a not in visited or node_b not in visited:
            unreachable = [node_id for node_id in [node_a, node_b] if node_id not in visited]
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"HLD cannot query disconnected node(s): {', '.join(unreachable)}",
                phase="result",
                state=base_state({"error": "disconnected query nodes"}),
            )
            return

        for current in reversed(dfs_order):
            best_child = None
            best_size = 0
            subtree_size[current] = 1
            for neighbor, _ in adjacency.get(current, []):
                if parent.get(neighbor) != current:
                    continue
                subtree_size[current] += subtree_size[neighbor]
                if subtree_size[neighbor] > best_size:
                    best_child = neighbor
                    best_size = subtree_size[neighbor]
            heavy_child[current] = best_child
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="visited",
                message=(
                    f"subtree_size({current}) = {subtree_size[current]}, "
                    f"heavy_child = {best_child or '(none)'}"
                ),
                phase="finalize",
                state=base_state({"current": current}),
            )

        current_position = 0

        def decompose(start: str, chain_head: str) -> Generator[Step, None, None]:
            nonlocal current_position
            head[start] = chain_head
            position[start] = current_position
            base_array.append(node_values[start])
            decomposition_order.append(start)
            chain_order.append(
                {
                    "node": start,
                    "head": chain_head,
                    "position": current_position,
                    "value": node_values[start],
                    "heavy_child": heavy_child.get(start),
                }
            )
            yield Step(
                action=StepAction.UPDATE_NODE_LABEL,
                target_type="node",
                target_id=start,
                value=f"{start}\nh={chain_head} pos={current_position}",
                message=f"Place {start} on chain headed by {chain_head} at position {current_position}",
                phase="relax",
                state=base_state({"current": start}),
            )
            current_position += 1

            heavy = heavy_child.get(start)
            if heavy is not None:
                yield from decompose(heavy, chain_head)

            for neighbor, _ in adjacency.get(start, []):
                if parent.get(neighbor) == start and neighbor != heavy:
                    yield from decompose(neighbor, neighbor)

        yield from decompose(root, root)

        def segment_sum(left: int, right: int) -> int:
            if left > right:
                left, right = right, left
            return sum(base_array[left : right + 1])

        segments: list[dict] = []
        u = node_a
        v = node_b
        while head[u] != head[v]:
            if depth[head[u]] < depth[head[v]]:
                u, v = v, u
            left = position[head[u]]
            right = position[u]
            value = segment_sum(left, right)
            segment = {"head": head[u], "from": head[u], "to": u, "left": left, "right": right, "value": value}
            segments.append(segment)
            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": [head[u], u], "edges": []},
                message=f"Take chain segment {head[u]} -> {u} positions [{left}, {right}] = {value}",
                phase="explore",
                state=base_state({"path_segments": list(segments), "current_segment": segment}),
            )
            u = parent[head[u]]
            if u is None:
                break

        if u is not None and v is not None:
            left = min(position[u], position[v])
            right = max(position[u], position[v])
            value = segment_sum(left, right)
            segment = {"head": head[u], "from": u, "to": v, "left": left, "right": right, "value": value}
            segments.append(segment)

        def path_to_root(node_id: str) -> list[str]:
            path: list[str] = []
            cursor: str | None = node_id
            while cursor is not None:
                path.append(cursor)
                cursor = parent.get(cursor)
            return path

        path_a = path_to_root(node_a)
        path_b = path_to_root(node_b)
        lca = next((node for node in path_a if node in set(path_b)), root)
        path_nodes = path_a[: path_a.index(lca) + 1] + list(reversed(path_b[: path_b.index(lca)]))
        path_edges: list[str] = []
        for child in path_a[: path_a.index(lca)]:
            path_edges.append(parent_edge[child])
        for child in reversed(path_b[: path_b.index(lca)]):
            path_edges.append(parent_edge[child])

        query_result = sum(segment["value"] for segment in segments)
        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": path_nodes, "edges": path_edges},
            message=f"HLD path sum {node_a} -> {node_b} = {query_result}",
            phase="result",
            state=base_state(
                {
                    "path_segments": segments,
                    "path_nodes": path_nodes,
                    "path_edges": path_edges,
                    "lca": lca,
                    "path_query_result": query_result,
                }
            ),
        )

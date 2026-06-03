"""Edmonds blossom algorithm for maximum cardinality matching in general graphs."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class BlossomMatchingAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="blossom_matching",
            category="graph",
            description="Maximum matching in a general undirected graph using Edmonds' blossom contraction",
            emoji="BM",
            parameters=[],
            requires_undirected=True,
            time_complexity="O(V^3)",
            space_complexity="O(V^2)",
            use_cases=[
                "General graph matching",
                "Pairing and scheduling with non-bipartite constraints",
                "Network design",
                "Combinatorial optimization",
            ],
            pseudocode=(
                "for each free root:\n"
                "    grow an alternating forest by BFS\n"
                "    if an edge joins two outer vertices:\n"
                "        find the least common ancestor\n"
                "        contract the odd cycle into a blossom\n"
                "    if a free vertex is reached:\n"
                "        augment along the alternating path\n"
                "return the matching"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        n = len(node_ids)
        if n == 0:
            return

        index = {node_id: i for i, node_id in enumerate(node_ids)}
        adjacency: list[list[int]] = [[] for _ in range(n)]
        edge_ids: dict[tuple[int, int], str] = {}

        for edge in graph.edges:
            if edge.source == edge.target:
                continue
            if edge.source not in index or edge.target not in index:
                continue
            u, v = index[edge.source], index[edge.target]
            if v not in adjacency[u]:
                adjacency[u].append(v)
            if u not in adjacency[v]:
                adjacency[v].append(u)
            key = (min(u, v), max(u, v))
            edge_ids[key] = edge.id or f"{edge.source}-{edge.target}"

        for neighbors in adjacency:
            neighbors.sort(key=lambda item: node_ids[item])

        match = [-1] * n
        augmenting_paths: list[list[str]] = []
        blossom_trace: list[dict] = []
        forest_trace: list[dict] = []

        def edge_id(u: int, v: int) -> str:
            return edge_ids.get((min(u, v), max(u, v)), f"{node_ids[u]}-{node_ids[v]}")

        def matching_rows() -> list[dict]:
            rows = []
            seen: set[tuple[int, int]] = set()
            for u, v in enumerate(match):
                if v == -1:
                    continue
                key = (min(u, v), max(u, v))
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"u": node_ids[key[0]], "v": node_ids[key[1]], "edge": edge_id(key[0], key[1])})
            return rows

        def state(extra: dict | None = None) -> dict:
            payload = {
                "matching_size": len(matching_rows()),
                "matching": matching_rows(),
                "free_vertices": [node_ids[i] for i, mate in enumerate(match) if mate == -1],
                "augmenting_paths": list(augmenting_paths),
                "blossom_trace": list(blossom_trace),
                "alternating_forest": list(forest_trace),
            }
            if extra:
                payload.update(extra)
            return payload

        def lca(a: int, b: int, base: list[int], parent: list[int]) -> int:
            used = [False] * n
            while True:
                a = base[a]
                used[a] = True
                if match[a] == -1:
                    break
                a = parent[match[a]]
            while True:
                b = base[b]
                if used[b]:
                    return b
                b = parent[match[b]]

        def mark_path(v: int, blossom_base: int, child: int, base: list[int], parent: list[int], blossom: list[bool]) -> None:
            while base[v] != blossom_base:
                blossom[base[v]] = True
                blossom[base[match[v]]] = True
                parent[v] = child
                child = match[v]
                v = parent[match[v]]

        def reconstruct_path(endpoint: int, parent: list[int]) -> list[int]:
            path = []
            v = endpoint
            while v != -1:
                path.append(v)
                pv = parent[v]
                if pv == -1:
                    break
                path.append(pv)
                v = match[pv]
            path.reverse()
            return path

        def find_path(root: int) -> tuple[int, list[int], list[dict]]:
            used = [False] * n
            parent = [-1] * n
            base = list(range(n))
            queue: deque[int] = deque([root])
            used[root] = True
            local_events: list[dict] = [{"type": "root", "root": node_ids[root]}]

            while queue:
                v = queue.popleft()
                local_events.append({"type": "dequeue", "vertex": node_ids[v], "base": node_ids[base[v]]})
                for u in adjacency[v]:
                    if base[v] == base[u] or match[v] == u:
                        continue

                    if u == root or (match[u] != -1 and parent[match[u]] != -1):
                        blossom_base = lca(v, u, base, parent)
                        blossom = [False] * n
                        mark_path(v, blossom_base, u, base, parent, blossom)
                        mark_path(u, blossom_base, v, base, parent, blossom)
                        contracted = sorted({node_ids[i] for i in range(n) if blossom[base[i]]})
                        event = {
                            "type": "blossom",
                            "edge": f"{node_ids[v]}-{node_ids[u]}",
                            "base": node_ids[blossom_base],
                            "contracted_vertices": contracted,
                        }
                        blossom_trace.append(event)
                        local_events.append(event)

                        for i in range(n):
                            if blossom[base[i]]:
                                base[i] = blossom_base
                                if not used[i]:
                                    used[i] = True
                                    queue.append(i)
                    elif parent[u] == -1:
                        parent[u] = v
                        tree_event = {"type": "tree_edge", "from": node_ids[v], "to": node_ids[u], "edge": edge_id(v, u)}
                        forest_trace.append(tree_event)
                        local_events.append(tree_event)
                        if match[u] == -1:
                            local_events.append({"type": "free_endpoint", "vertex": node_ids[u]})
                            return u, parent, local_events

                        mate = match[u]
                        used[mate] = True
                        queue.append(mate)
                        local_events.append({"type": "follow_matched_edge", "from": node_ids[u], "to": node_ids[mate], "edge": edge_id(u, mate)})

            return -1, parent, local_events

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Start Edmonds blossom matching on {n} vertices",
            phase="init",
            state=state(),
        )

        for root in range(n):
            if match[root] != -1:
                continue

            endpoint, parent, events = find_path(root)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=node_ids[root],
                value="current",
                message=f"Grow alternating forest from free vertex {node_ids[root]}",
                phase="explore",
                state=state({"current_root": node_ids[root], "search_events": events}),
            )

            if endpoint == -1:
                continue

            path = reconstruct_path(endpoint, parent)
            path_nodes = [node_ids[i] for i in path]
            path_edges = [edge_id(path[i], path[i + 1]) for i in range(len(path) - 1)]

            v = endpoint
            while v != -1:
                pv = parent[v]
                if pv == -1:
                    break
                nv = match[pv]
                match[v] = pv
                match[pv] = v
                v = nv

            augmenting_paths.append(path_nodes)
            yield Step(
                action=StepAction.MARK_PATH,
                target_type="node",
                target_id="",
                value={"nodes": path_nodes, "edges": path_edges},
                message=f"Augment along {' -> '.join(path_nodes)}",
                phase="relax",
                state=state({"augmenting_path": path_nodes, "augmenting_edges": path_edges}),
            )
            for item in path_edges:
                yield Step(
                    action=StepAction.SET_EDGE_COLOR,
                    target_type="edge",
                    target_id=item,
                    value="path",
                    message="Mark matched edge after augmentation",
                    phase="relax",
                    state=state(),
                )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Blossom matching complete. Matching size = {len(matching_rows())}",
            phase="result",
            state=state(),
        )

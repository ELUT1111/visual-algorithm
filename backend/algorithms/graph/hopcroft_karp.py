"""Hopcroft-Karp maximum bipartite matching visualization."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class HopcroftKarpAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="hopcroft_karp",
            category="graph",
            description="Maximum bipartite matching with layered BFS and DFS augmentation",
            emoji="HK",
            parameters=[],
            requires_undirected=True,
            time_complexity="O(E sqrt(V))",
            space_complexity="O(V + E)",
            use_cases=[
                "Bipartite matching",
                "Job assignment feasibility",
                "Course-seat allocation",
                "Maximum cardinality matching",
            ],
            pseudocode=(
                "while BFS builds layers from free left vertices:\n"
                "    for each free left vertex u:\n"
                "        if DFS finds an augmenting path from u:\n"
                "            matching += 1"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        nodes = [node.id for node in graph.nodes]
        if not nodes:
            return

        metadata_side = {
            node.id: str(node.metadata.get("partition", node.metadata.get("side", ""))).upper()
            for node in graph.nodes
        }
        left = sorted([node_id for node_id, side in metadata_side.items() if side in {"L", "LEFT", "A"}])
        right = sorted([node_id for node_id, side in metadata_side.items() if side in {"R", "RIGHT", "B"}])

        adjacency_all: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in nodes}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency_all.setdefault(edge.source, []).append((edge.target, edge_id))
            adjacency_all.setdefault(edge.target, []).append((edge.source, edge_id))

        if not left or not right:
            colors: dict[str, int] = {}
            for start in nodes:
                if start in colors:
                    continue
                colors[start] = 0
                queue = deque([start])
                while queue:
                    current = queue.popleft()
                    for neighbor, _ in adjacency_all.get(current, []):
                        if neighbor not in colors:
                            colors[neighbor] = 1 - colors[current]
                            queue.append(neighbor)
            left = sorted([node_id for node_id, color in colors.items() if color == 0])
            right = sorted([node_id for node_id, color in colors.items() if color == 1])

        left_set = set(left)
        right_set = set(right)
        adjacency: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in left}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            if edge.source in left_set and edge.target in right_set:
                adjacency[edge.source].append((edge.target, edge_id))
            elif edge.target in left_set and edge.source in right_set:
                adjacency[edge.target].append((edge.source, edge_id))

        pair_u: dict[str, str | None] = {u: None for u in left}
        pair_v: dict[str, str | None] = {v: None for v in right}
        dist: dict[str, int] = {}
        matching_edges: dict[tuple[str, str], str] = {}

        def state(extra: dict | None = None) -> dict:
            payload = {
                "left_partition": left,
                "right_partition": right,
                "matching": [{"left": u, "right": v} for u, v in pair_u.items() if v is not None],
                "matching_size": sum(1 for v in pair_u.values() if v is not None),
                "layers": dict(dist),
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Start Hopcroft-Karp with partitions {len(left)} and {len(right)}",
            phase="init",
            state=state(),
        )

        def bfs() -> bool:
            queue: deque[str] = deque()
            found_free_right = False
            for u in left:
                if pair_u[u] is None:
                    dist[u] = 0
                    queue.append(u)
                else:
                    dist[u] = -1

            while queue:
                u = queue.popleft()
                for v, _ in adjacency.get(u, []):
                    mate = pair_v.get(v)
                    if mate is None:
                        found_free_right = True
                    elif dist.get(mate, -1) < 0:
                        dist[mate] = dist[u] + 1
                        queue.append(mate)
            return found_free_right

        def dfs(u: str, path: list[tuple[str, str, str]]) -> bool:
            for v, edge_id in adjacency.get(u, []):
                mate = pair_v.get(v)
                path.append((u, v, edge_id))
                if mate is None or (dist.get(mate, -1) == dist[u] + 1 and dfs(mate, path)):
                    pair_u[u] = v
                    pair_v[v] = u
                    matching_edges[(u, v)] = edge_id
                    return True
                path.pop()
            dist[u] = -1
            return False

        phase_no = 0
        while bfs():
            phase_no += 1
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"BFS phase {phase_no} built alternating layers",
                phase="explore",
                state=state({"phase": phase_no, "free_left": [u for u in left if pair_u[u] is None]}),
            )
            for u in left:
                if pair_u[u] is not None:
                    continue
                path: list[tuple[str, str, str]] = []
                if dfs(u, path):
                    path_nodes = [path[0][0]] + [v for _, v, _ in path]
                    path_edges = [edge_id for _, _, edge_id in path]
                    yield Step(
                        action=StepAction.MARK_PATH,
                        target_type="node",
                        target_id="",
                        value={"nodes": path_nodes, "edges": path_edges},
                        message=f"Augment matching along {' -> '.join(path_nodes)}",
                        phase="relax",
                        state=state({"augmenting_path": path_nodes}),
                    )
                    for edge_id in path_edges:
                        yield Step(
                            action=StepAction.SET_EDGE_COLOR,
                            target_type="edge",
                            target_id=edge_id,
                            value="path",
                            message="Mark matched edge",
                            phase="relax",
                            state=state(),
                        )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Hopcroft-Karp complete. Matching size = {state()['matching_size']}",
            phase="result",
            state=state(),
        )

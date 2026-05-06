"""A* shortest path algorithm."""
from __future__ import annotations

import heapq
import math
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class AStarAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="astar",
            category="graph",
            description="A* search with heuristic for shortest path",
            emoji="⭐",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Start node ID"},
                {"name": "target", "type": "str", "required": True, "description": "Goal node ID"},
            ],
            requires_weighted=True,
            time_complexity="O(E) best, O(b^d) worst",
            space_complexity="O(V)",
            use_cases=[
                "Game pathfinding (NPCs, RTS)",
                "Robot navigation and motion planning",
                "Map routing with heuristics",
                "Puzzle solving (8-puzzle, Rubik's cube)",
            ],
            pseudocode=(
                "function AStar(graph, source, target, h):\n"
                "    g[source] = 0\n"
                "    f[source] = h(source, target)\n"
                "    openSet = {source}\n"
                "    while openSet is not empty:\n"
                "        current = node in openSet with min f[]\n"
                "        if current == target:\n"
                "            return reconstruct_path()\n"
                "        remove current from openSet\n"
                "        for each neighbor of current:\n"
                "            tentative_g = g[current] + weight(current, neighbor)\n"
                "            if tentative_g < g[neighbor]:\n"
                "                g[neighbor] = tentative_g\n"
                "                f[neighbor] = g[neighbor] + h(neighbor, target)\n"
                "                add neighbor to openSet\n"
                "    return null  // no path found"
            ),
        )

    def _heuristic(self, node_id, target_id, node_positions):
        """Euclidean distance heuristic using node positions."""
        pos1 = node_positions.get(node_id, (0, 0))
        pos2 = node_positions.get(target_id, (0, 0))
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    def run(self, graph, params) -> Generator[Step, None, None]:
        source = params.get("source")
        target = params.get("target")
        if not source or not target:
            return

        # Build adjacency list
        adj: dict[str, list[tuple[str, float, str]]] = {n.id: [] for n in graph.nodes}
        node_positions = {}
        for n in graph.nodes:
            node_positions[n.id] = (n.x or 0, n.y or 0)

        for e in graph.edges:
            adj.setdefault(e.source, []).append((e.target, e.weight, e.id))
            if not graph.directed:
                adj.setdefault(e.target, []).append((e.source, e.weight, e.id))

        g_score = {n.id: float("inf") for n in graph.nodes}
        g_score[source] = 0
        f_score = {n.id: float("inf") for n in graph.nodes}
        f_score[source] = self._heuristic(source, target, node_positions)
        prev = {n.id: None for n in graph.nodes}
        closed = set()

        # Priority queue: (f_score, node_id)
        open_set = [(f_score[source], source)]
        open_set_lookup = {source}

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Starting A* from {source} to {target}",
            phase="init",
        )

        # Show heuristic values
        for n in graph.nodes:
            h = self._heuristic(n.id, target, node_positions)
            if n.id == source:
                yield Step(
                    action=StepAction.UPDATE_NODE_LABEL,
                    target_type="node",
                    target_id=n.id,
                    value=f"{n.id}\ng=0 h={h:.1f}",
                    message=f"Node {n.id}: g=0, h={h:.1f}, f={h:.1f}",
                    phase="init",
                )
            else:
                yield Step(
                    action=StepAction.UPDATE_NODE_LABEL,
                    target_type="node",
                    target_id=n.id,
                    value=f"{n.id}\nh={h:.1f}",
                    message=f"Heuristic for {n.id}: h={h:.1f}",
                    phase="init",
                )

        while open_set:
            _, current = heapq.heappop(open_set)
            open_set_lookup.discard(current)

            if current in closed:
                continue

            closed.add(current)

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Exploring node {current} (g={g_score[current]:.1f}, f={f_score[current]:.1f})",
                phase="explore",
            )

            if current == target:
                # Trace path
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = prev[node]
                path.reverse()

                yield Step(
                    action=StepAction.MARK_PATH,
                    target_type="node",
                    target_id="",
                    value=path,
                    message=f"Path found! {' → '.join(path)} (cost={g_score[target]:.1f})",
                    phase="result",
                )
                return

            for neighbor, weight, edge_id in adj.get(current, []):
                if neighbor in closed:
                    continue

                tentative_g = g_score[current] + weight
                h = self._heuristic(neighbor, target, node_positions)

                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Checking {current} → {neighbor} (weight={weight})",
                    phase="relax",
                )

                if tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + h
                    prev[neighbor] = current

                    yield Step(
                        action=StepAction.UPDATE_NODE_LABEL,
                        target_type="node",
                        target_id=neighbor,
                        value=f"{neighbor}\ng={tentative_g:.1f} h={h:.1f}",
                        message=f"Updated {neighbor}: g={tentative_g:.1f}, h={h:.1f}, f={f_score[neighbor]:.1f}",
                        phase="relax",
                    )

                    if neighbor not in open_set_lookup:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_lookup.add(neighbor)

                        yield Step(
                            action=StepAction.SET_NODE_COLOR,
                            target_type="node",
                            target_id=neighbor,
                            value="exploring",
                            message=f"Added {neighbor} to open set",
                            phase="relax",
                        )

                yield Step(
                    action=StepAction.UNHIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    message="",
                    phase="relax",
                )

            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="settled",
                message=f"Node {current} closed",
                phase="finalize",
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"No path found from {source} to {target}",
            phase="result",
        )

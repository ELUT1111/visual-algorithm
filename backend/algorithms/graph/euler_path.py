"""Euler path and circuit detection with Hierholzer's algorithm."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class EulerPathAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="euler_path",
            category="graph",
            description="Find an Euler path or circuit that uses every edge exactly once",
            emoji="EP",
            parameters=[
                {"name": "start", "type": "str", "required": False, "default": "", "description": "Optional start node ID"},
            ],
            time_complexity="O(V + E)",
            space_complexity="O(V + E)",
            use_cases=[
                "Route inspection and street sweeping",
                "DNA fragment assembly with de Bruijn graphs",
                "Drawing a graph without lifting the pen",
                "Validating edge-covering traversal plans",
            ],
            pseudocode=(
                "check Euler degree conditions\n"
                "choose a valid start vertex\n"
                "stack = [start]\n"
                "while stack is not empty:\n"
                "    if top has unused incident edge:\n"
                "        consume edge and push neighbor\n"
                "    else:\n"
                "        pop top into output path\n"
                "return reversed output path"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        for edge in graph.edges:
            if edge.source not in node_ids:
                node_ids.append(edge.source)
            if edge.target not in node_ids:
                node_ids.append(edge.target)
        if not node_ids:
            return

        requested_start = str(params.get("start", "") or "").strip() or None
        edge_count = len(graph.edges)
        directed = bool(graph.directed)

        adjacency: dict[str, list[tuple[str, int, str]]] = {node_id: [] for node_id in node_ids}
        weak_adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
        in_degree: dict[str, int] = {node_id: 0 for node_id in node_ids}
        out_degree: dict[str, int] = {node_id: 0 for node_id in node_ids}
        degree: dict[str, int] = {node_id: 0 for node_id in node_ids}

        for index, edge in enumerate(graph.edges):
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, index, edge_id))
            weak_adjacency.setdefault(edge.source, set()).add(edge.target)
            weak_adjacency.setdefault(edge.target, set()).add(edge.source)
            out_degree[edge.source] = out_degree.get(edge.source, 0) + 1
            in_degree[edge.target] = in_degree.get(edge.target, 0) + 1

            if directed:
                degree[edge.source] = degree.get(edge.source, 0) + 1
                degree[edge.target] = degree.get(edge.target, 0) + 1
            else:
                adjacency.setdefault(edge.target, []).append((edge.source, index, edge_id))
                degree[edge.source] = degree.get(edge.source, 0) + 1
                degree[edge.target] = degree.get(edge.target, 0) + 1

        def degree_summary() -> dict:
            if directed:
                return {
                    node_id: {
                        "in": in_degree.get(node_id, 0),
                        "out": out_degree.get(node_id, 0),
                        "diff": out_degree.get(node_id, 0) - in_degree.get(node_id, 0),
                    }
                    for node_id in node_ids
                }
            return {node_id: degree.get(node_id, 0) for node_id in node_ids}

        def base_state(extra: dict | None = None) -> dict:
            payload = {
                "directed": directed,
                "mode": mode,
                "start": start,
                "edge_count": edge_count,
                "used_edge_count": len(used_edges),
                "degree_summary": degree_summary(),
                "is_eulerian": is_eulerian,
                "failure_reason": failure_reason,
            }
            if directed:
                payload["in_degree"] = dict(in_degree)
                payload["out_degree"] = dict(out_degree)
            else:
                payload["degree"] = dict(degree)
                payload["odd_degree_nodes"] = list(odd_nodes)
            if extra:
                payload.update(extra)
            return payload

        mode = "circuit"
        start: str | None = None
        failure_reason = ""
        is_eulerian = True
        odd_nodes: list[str] = []
        used_edges: set[int] = set()

        nonzero_nodes = [node_id for node_id in node_ids if degree.get(node_id, 0) > 0]
        if directed:
            start_candidates: list[str] = []
            end_candidates: list[str] = []
            invalid_degree_nodes: list[str] = []
            for node_id in node_ids:
                diff = out_degree.get(node_id, 0) - in_degree.get(node_id, 0)
                if diff == 1:
                    start_candidates.append(node_id)
                elif diff == -1:
                    end_candidates.append(node_id)
                elif diff != 0:
                    invalid_degree_nodes.append(node_id)

            if invalid_degree_nodes or not (
                (len(start_candidates) == 0 and len(end_candidates) == 0)
                or (len(start_candidates) == 1 and len(end_candidates) == 1)
            ):
                is_eulerian = False
                failure_reason = "Directed Euler path needs matching in/out degree differences of 0, or exactly one +1 start and one -1 end."
            elif start_candidates:
                mode = "path"
                start = start_candidates[0]
            else:
                start = nonzero_nodes[0] if nonzero_nodes else node_ids[0]
        else:
            odd_nodes = [node_id for node_id in node_ids if degree.get(node_id, 0) % 2 == 1]
            if len(odd_nodes) not in (0, 2):
                is_eulerian = False
                failure_reason = "Undirected Euler path needs exactly 0 or 2 odd-degree nodes."
            elif len(odd_nodes) == 2:
                mode = "path"
                start = odd_nodes[0]
            else:
                start = nonzero_nodes[0] if nonzero_nodes else node_ids[0]

        if requested_start is not None:
            if requested_start not in node_ids:
                is_eulerian = False
                failure_reason = f"Start node {requested_start} does not exist."
            elif edge_count > 0 and degree.get(requested_start, 0) == 0:
                is_eulerian = False
                failure_reason = f"Start node {requested_start} has no incident edges."
            elif directed and mode == "path" and requested_start != start:
                is_eulerian = False
                failure_reason = f"Directed Euler path must start at {start}."
            elif not directed and mode == "path" and requested_start not in odd_nodes:
                is_eulerian = False
                failure_reason = f"Undirected Euler path must start at one of the odd-degree nodes: {', '.join(odd_nodes)}."
            else:
                start = requested_start

        if is_eulerian and edge_count > 0 and start is not None:
            seen = {start}
            stack = [start]
            while stack:
                current = stack.pop()
                for neighbor in weak_adjacency.get(current, set()):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)
            disconnected = [node_id for node_id in nonzero_nodes if node_id not in seen]
            if disconnected:
                is_eulerian = False
                failure_reason = f"All non-isolated vertices must be connected; unreachable: {', '.join(disconnected)}."

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Euler {mode} check from {start}: {edge_count} edge(s)",
            phase="init",
            state=base_state(),
        )

        for node_id in node_ids:
            if directed:
                label = f"{node_id}\nin={in_degree.get(node_id, 0)} out={out_degree.get(node_id, 0)}"
                message = f"{node_id}: in={in_degree.get(node_id, 0)}, out={out_degree.get(node_id, 0)}"
            else:
                label = f"{node_id}\ndeg={degree.get(node_id, 0)}"
                message = f"{node_id}: degree={degree.get(node_id, 0)}"
            yield Step(
                action=StepAction.UPDATE_NODE_LABEL,
                target_type="node",
                target_id=node_id,
                value=label,
                message=message,
                phase="init",
                state=base_state({"current": node_id}),
            )

        if not is_eulerian or start is None:
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=f"No Euler path: {failure_reason}",
                phase="result",
                state=base_state({"euler_path": [], "euler_edges": []}),
            )
            return

        node_stack: list[str] = [start]
        edge_stack: list[str | None] = [None]
        path_reversed: list[str] = []
        edge_path_reversed: list[str] = []

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=start,
            value="current",
            message=f"Start Hierholzer traversal at {start}",
            phase="explore",
            state=base_state({"stack": list(node_stack), "euler_path": []}),
        )

        while node_stack:
            current = node_stack[-1]
            while adjacency.get(current) and adjacency[current][-1][1] in used_edges:
                adjacency[current].pop()

            if adjacency.get(current):
                neighbor, edge_index, edge_id = adjacency[current].pop()
                if edge_index in used_edges:
                    continue
                used_edges.add(edge_index)
                node_stack.append(neighbor)
                edge_stack.append(edge_id)
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge_id,
                    value="exploring",
                    message=f"Consume edge {edge_id}: move {current} -> {neighbor}",
                    phase="explore",
                    state=base_state({
                        "current": neighbor,
                        "stack": list(node_stack),
                        "last_edge": edge_id,
                        "euler_path": list(reversed(path_reversed)),
                        "euler_edges": list(reversed(edge_path_reversed)),
                    }),
                )
                continue

            finished = node_stack.pop()
            incoming_edge = edge_stack.pop()
            path_reversed.append(finished)
            if incoming_edge is not None:
                edge_path_reversed.append(incoming_edge)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=finished,
                value="visited",
                message=f"Backtrack from {finished}; prepend it to the Euler {mode}",
                phase="finalize",
                state=base_state({
                    "current": finished,
                    "stack": list(node_stack),
                    "euler_path": list(reversed(path_reversed)),
                    "euler_edges": list(reversed(edge_path_reversed)),
                }),
            )

        euler_path = list(reversed(path_reversed))
        euler_edges = list(reversed(edge_path_reversed))
        is_complete = len(euler_edges) == edge_count
        if not is_complete:
            failure_reason = "Traversal ended before every edge was consumed."
            is_eulerian = False

        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": euler_path, "edges": euler_edges},
            message=f"Euler {mode}: {' -> '.join(euler_path)}" if is_complete else f"No Euler path: {failure_reason}",
            phase="result",
            state=base_state({
                "euler_path": euler_path,
                "euler_edges": euler_edges,
                "used_edge_count": len(euler_edges),
                "is_eulerian": is_complete,
                "failure_reason": "" if is_complete else failure_reason,
            }),
        )

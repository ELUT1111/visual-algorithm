"""Dominator tree and dominance frontier for directed control-flow graphs."""
from __future__ import annotations

from collections import deque
from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class DominatorTreeAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="dominator_tree",
            category="graph",
            description="Compute immediate dominators, the dominator tree, and dominance frontiers in a directed graph",
            emoji="DT",
            parameters=[
                {
                    "name": "source",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "Entry node ID; defaults to graph root or the first node",
                }
            ],
            requires_directed=True,
            time_complexity="O(V * E) iterative data-flow",
            space_complexity="O(V^2)",
            use_cases=[
                "Compiler control-flow analysis",
                "SSA phi-node placement",
                "Program slicing and optimization",
                "Workflow bottleneck and mandatory checkpoint analysis",
            ],
            pseudocode=(
                "dom[start] = {start}\n"
                "for every other reachable vertex v: dom[v] = all vertices\n"
                "repeat until no set changes:\n"
                "    for each v != start:\n"
                "        dom[v] = {v} union intersection(dom[p] for p in predecessors[v])\n"
                "idom[v] = closest strict dominator of v\n"
                "build tree edges idom[v] -> v\n"
                "compute dominance frontier from join predecessors"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        node_ids = [node.id for node in graph.nodes]
        if not node_ids:
            return

        requested_source = str(params.get("source", "") or "").strip()
        source = requested_source or graph.root_id or node_ids[0]
        if source not in node_ids:
            source = node_ids[0]

        adjacency: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in node_ids}
        predecessors: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        edge_ids: dict[tuple[str, str], list[str]] = {}
        for edge in graph.edges:
            edge_id = edge.id or f"{edge.source}-{edge.target}"
            adjacency.setdefault(edge.source, []).append((edge.target, edge_id))
            predecessors.setdefault(edge.target, []).append(edge.source)
            edge_ids.setdefault((edge.source, edge.target), []).append(edge_id)

        reachable: list[str] = []
        seen = {source}
        queue = deque([source])
        while queue:
            current = queue.popleft()
            reachable.append(current)
            for neighbor, _ in adjacency.get(current, []):
                if neighbor in seen or neighbor not in node_ids:
                    continue
                seen.add(neighbor)
                queue.append(neighbor)

        reachable_set = set(reachable)
        unreachable = [node_id for node_id in node_ids if node_id not in reachable_set]

        dominators: dict[str, set[str]] = {}
        for node_id in node_ids:
            if node_id == source:
                dominators[node_id] = {source}
            elif node_id in reachable_set:
                dominators[node_id] = set(reachable)
            else:
                dominators[node_id] = set()

        iterations: list[dict] = []

        def ordered(values: set[str] | list[str]) -> list[str]:
            value_set = set(values)
            return [node_id for node_id in node_ids if node_id in value_set]

        def display_dominators() -> dict[str, list[str]]:
            return {node_id: ordered(dominators[node_id]) for node_id in node_ids}

        def state(extra: dict | None = None) -> dict:
            payload = {
                "source": source,
                "reachable_nodes": list(reachable),
                "unreachable_nodes": list(unreachable),
                "predecessors": {
                    node_id: [pred for pred in predecessors.get(node_id, []) if pred in reachable_set]
                    for node_id in reachable
                },
                "dominators": display_dominators(),
                "iterations": list(iterations),
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id=source,
            message=f"Start dominator analysis from entry {source}",
            phase="init",
            state=state(),
        )

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"{source} dominates only itself at initialization",
            phase="init",
            state=state({"current": source}),
        )

        changed = True
        pass_number = 0
        while changed:
            changed = False
            pass_number += 1
            pass_changes: list[dict] = []

            for node_id in reachable:
                if node_id == source:
                    continue

                valid_predecessors = [pred for pred in predecessors.get(node_id, []) if pred in reachable_set]
                if valid_predecessors:
                    intersection = set(dominators[valid_predecessors[0]])
                    for pred in valid_predecessors[1:]:
                        intersection &= dominators[pred]
                    next_dominators = intersection | {node_id}
                else:
                    next_dominators = {node_id}

                yield Step(
                    action=StepAction.HIGHLIGHT_NODE,
                    target_type="node",
                    target_id=node_id,
                    value="exploring",
                    message=f"Recompute dominators of {node_id} from predecessors {', '.join(valid_predecessors) or 'none'}",
                    phase="explore",
                    state=state(
                        {
                            "current": node_id,
                            "iteration": pass_number,
                            "candidate_dominators": ordered(next_dominators),
                        }
                    ),
                )

                if next_dominators != dominators[node_id]:
                    before = ordered(dominators[node_id])
                    dominators[node_id] = next_dominators
                    changed = True
                    change = {"node": node_id, "before": before, "after": ordered(next_dominators)}
                    pass_changes.append(change)
                    yield Step(
                        action=StepAction.UPDATE_NODE_LABEL,
                        target_type="node",
                        target_id=node_id,
                        value=f"{node_id}\ndom={{{', '.join(change['after'])}}}",
                        message=f"Update dom({node_id}) to {{{', '.join(change['after'])}}}",
                        phase="relax",
                        state=state({"current": node_id, "iteration": pass_number, "change": change}),
                    )

            iterations.append({"pass": pass_number, "changed_nodes": [change["node"] for change in pass_changes]})
            yield Step(
                action=StepAction.ADD_MESSAGE,
                target_type="node",
                target_id="",
                message=(
                    f"Pass {pass_number} changed {', '.join(change['node'] for change in pass_changes)}"
                    if pass_changes
                    else f"Pass {pass_number} made no changes; dominator sets converged"
                ),
                phase="finalize",
                state=state({"iteration": pass_number, "pass_changes": pass_changes}),
            )

        immediate_dominators: dict[str, str | None] = {source: None}
        for node_id in reachable:
            if node_id == source:
                continue
            strict_dominators = dominators[node_id] - {node_id}
            immediate = None
            for candidate in sorted(strict_dominators, key=lambda item: node_ids.index(item)):
                if all(candidate not in dominators[other] for other in strict_dominators if other != candidate):
                    immediate = candidate
                    break
            immediate_dominators[node_id] = immediate

        dominator_tree = [
            {
                "source": parent,
                "target": node_id,
                "edge": f"{parent}->{node_id}",
            }
            for node_id, parent in immediate_dominators.items()
            if parent is not None
        ]

        dominance_frontier: dict[str, set[str]] = {node_id: set() for node_id in reachable}
        for node_id in reachable:
            valid_predecessors = [pred for pred in predecessors.get(node_id, []) if pred in reachable_set]
            if len(valid_predecessors) < 2:
                continue
            for pred in valid_predecessors:
                runner = pred
                while runner is not None and runner != immediate_dominators.get(node_id):
                    dominance_frontier[runner].add(node_id)
                    runner = immediate_dominators.get(runner)

        result_state = state(
            {
                "immediate_dominators": {
                    node_id: parent for node_id, parent in immediate_dominators.items() if parent is not None
                },
                "dominator_tree": dominator_tree,
                "dominance_frontier": {
                    node_id: ordered(frontier) for node_id, frontier in dominance_frontier.items()
                },
            }
        )

        for tree_edge in dominator_tree:
            original_edges = edge_ids.get((tree_edge["source"], tree_edge["target"]), [])
            if original_edges:
                yield Step(
                    action=StepAction.SET_EDGE_COLOR,
                    target_type="edge",
                    target_id=original_edges[0],
                    value="path",
                    message=f"Immediate dominator: {tree_edge['source']} dominates {tree_edge['target']}",
                    phase="result",
                    state=result_state,
                )

        yield Step(
            action=StepAction.MARK_PATH,
            target_type="node",
            target_id="",
            value={"nodes": reachable, "edges": [edge["edge"] for edge in dominator_tree]},
            message=f"Dominator tree complete with {len(dominator_tree)} edges",
            phase="result",
            state=result_state,
        )

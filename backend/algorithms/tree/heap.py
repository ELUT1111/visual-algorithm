"""Heap - build a max-heap or min-heap with sift-up visualization."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class HeapAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="heap",
            category="tree",
            description="Build a max-heap or min-heap from values with sift-up",
            emoji="🏔️",
            parameters=[
                {"name": "values", "type": "str", "required": True,
                 "description": "Comma-separated values to insert (e.g. 4,10,3,5,1)"},
                {"name": "type", "type": "str", "required": False, "default": "max",
                 "description": "Heap type: max (default) or min"},
            ],
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
            use_cases=[
                "Priority queue implementation",
                "Heap sort algorithm",
                "Finding k-th largest/smallest element",
                "Task scheduling by priority",
                "Dijkstra's algorithm optimization",
            ],
            pseudocode=(
                "function BuildHeap(arr, type):\n"
                "    heap = []\n"
                "    for each value in arr:\n"
                "        heap.append(value)\n"
                "        sift_up(heap, len(heap) - 1, type)\n"
                "\n"
                "function sift_up(heap, i, type):\n"
                "    while i > 0:\n"
                "        parent = (i - 1) / 2\n"
                "        if should_swap(heap[i], heap[parent], type):\n"
                "            swap(heap[i], heap[parent])\n"
                "            i = parent\n"
                "        else: break"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        values_str = params.get("values", "")
        if not values_str:
            return

        try:
            values = [int(v.strip()) for v in values_str.split(",") if v.strip()]
        except ValueError:
            values = [v.strip() for v in values_str.split(",") if v.strip()]

        if not values:
            return

        heap_type = params.get("type", "max").strip().lower()
        is_max = heap_type != "min"
        type_label = "Max-Heap" if is_max else "Min-Heap"

        def should_swap(child_val, parent_val):
            if is_max:
                return child_val > parent_val
            else:
                return child_val < parent_val

        # Array-based heap: heap[i] = node_id
        heap: list[str] = []
        node_values: dict[str, any] = {}
        node_counter = 0
        # Track ALL edge IDs ever created so we can remove them reliably
        edge_ids: set[str] = set()

        # Layout constants
        LEVEL_H = 100   # vertical spacing between levels
        NODE_W = 120    # horizontal spacing between nodes at deepest level

        def make_id():
            nonlocal node_counter
            node_counter += 1
            return f"h{node_counter}"

        def parent_idx(i):
            return (i - 1) // 2

        import math

        def node_pos(idx):
            """Compute (x, y) for heap index idx using binary tree layout."""
            if idx == 0:
                return (0, 0)
            level = int(math.log2(idx + 1))
            pos_in_level = idx - (2 ** level - 1)
            nodes_in_level = 2 ** level
            # Center each level, spread nodes evenly
            total_width = nodes_in_level * NODE_W
            x = -total_width / 2 + (pos_in_level + 0.5) * NODE_W
            y = level * LEVEL_H
            return (x, y)

        def emit_positions():
            """Yield UPDATE_NODE_POSITION steps for ALL nodes in the heap."""
            for i, nid in enumerate(heap):
                x, y = node_pos(i)
                yield Step(
                    action=StepAction.UPDATE_NODE_POSITION,
                    target_type="node",
                    target_id=nid,
                    value={"x": x, "y": y},
                    message="", phase="relax",
                )

        def rebuild_edges():
            """Remove ALL edges then rebuild from current heap array."""
            # Remove every edge we ever created
            for eid in list(edge_ids):
                yield Step(
                    action=StepAction.REMOVE_EDGE,
                    target_type="edge",
                    target_id=eid,
                    value=None, message="", phase="relax",
                )
            edge_ids.clear()

            # Re-add edges based on current heap array
            for i in range(len(heap)):
                li = 2 * i + 1
                ri = 2 * i + 2
                if li < len(heap):
                    eid = f"{heap[i]}-{heap[li]}"
                    edge_ids.add(eid)
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=eid,
                        value={"source": heap[i], "target": heap[li], "label": ""},
                        message="", phase="relax",
                    )
                if ri < len(heap):
                    eid = f"{heap[i]}-{heap[ri]}"
                    edge_ids.add(eid)
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=eid,
                        value={"source": heap[i], "target": heap[ri], "label": ""},
                        message="", phase="relax",
                    )

            # Re-position all nodes after swap
            yield from emit_positions()

        def update_label(idx):
            nid = heap[idx]
            val = node_values[nid]
            yield Step(
                action=StepAction.UPDATE_NODE_LABEL,
                target_type="node",
                target_id=nid,
                value=str(val),
                message=f"[{idx}] = {val}",
                phase="relax",
            )

        def sift_up(i):
            """Sift element at index i up to restore heap property."""
            while i > 0:
                pi = parent_idx(i)
                child_id = heap[i]
                parent_id = heap[pi]
                child_val = node_values[child_id]
                parent_val = node_values[parent_id]

                # Highlight comparison
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=child_id,
                    value="current",
                    message=f"Compare [{i}]={child_val} with parent [{pi}]={parent_val}",
                    phase="explore",
                )
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=parent_id,
                    value="exploring",
                    message="",
                    phase="explore",
                )

                if should_swap(child_val, parent_val):
                    # Swap in array
                    heap[i], heap[pi] = heap[pi], heap[i]

                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=child_id,
                        value="path",
                        message=f"Swap: {child_val} <-> {parent_val}",
                        phase="explore",
                    )
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=parent_id,
                        value="path",
                        message="",
                        phase="explore",
                    )

                    # Rebuild edges after swap (removes ALL old edges, creates correct ones)
                    yield from rebuild_edges()

                    # Update labels to reflect new positions
                    yield from update_label(i)
                    yield from update_label(pi)

                    # Mark settled
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=heap[i],
                        value="visited",
                        message="",
                        phase="relax",
                    )

                    i = pi
                else:
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=child_id,
                        value="visited",
                        message=f"Heap property satisfied at [{i}]",
                        phase="relax",
                    )
                    break

            # Mark root if we reached it
            if i == 0:
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=heap[0],
                    value="mst",
                    message="",
                    phase="relax",
                )

        # --- Main loop ---
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Building {type_label} from: {values_str}",
            phase="init",
        )

        for val in values:
            nid = make_id()
            idx = len(heap)
            heap.append(nid)
            node_values[nid] = val

            # Compute exact position from heap index
            x, y = node_pos(idx)

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=nid,
                value={"id": nid, "label": str(val), "x": x, "y": y},
                message=f"Insert {val} at position [{idx}]",
                phase="init",
            )

            # Add edge to parent immediately
            if idx > 0:
                pi = parent_idx(idx)
                pid = heap[pi]
                eid = f"{pid}-{nid}"
                edge_ids.add(eid)
                yield Step(
                    action=StepAction.ADD_EDGE,
                    target_type="edge",
                    target_id=eid,
                    value={"source": pid, "target": nid, "label": ""},
                    message="", phase="relax",
                )

            # Highlight new node
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=nid,
                value="current",
                message=f"Sift up {val} from [{idx}]",
                phase="explore",
            )

            # Sift up
            yield from sift_up(idx)

        # Final: highlight root
        if heap:
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=heap[0],
                value="path",
                message=f"{'Maximum' if is_max else 'Minimum'} element: {node_values[heap[0]]}",
                phase="result",
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"{type_label} complete. {len(values)} elements.",
            phase="result",
        )

"""Huffman Coding tree construction."""
from __future__ import annotations

import heapq
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class HuffmanAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="huffman",
            category="tree",
            description="Build a Huffman coding tree for data compression",
            emoji="📦",
            parameters=[
                {"name": "text", "type": "str", "required": True,
                 "description": "Input text to build Huffman tree (e.g. hello world)"},
            ],
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
            use_cases=[
                "Data compression (ZIP, GZIP)",
                "Huffman encoding/decoding",
                "Prefix-free codes",
                "Telecommunications",
                "File compression algorithms",
            ],
            pseudocode=(
                "function Huffman(text):\n"
                "    freq = count_frequencies(text)\n"
                "    heap = create_min_heap(freq)\n"
                "    while len(heap) > 1:\n"
                "        left = heap.extract_min()\n"
                "        right = heap.extract_min()\n"
                "        merged = new Node(left.freq + right.freq)\n"
                "        merged.left = left\n"
                "        merged.right = right\n"
                "        heap.insert(merged)\n"
                "    return heap.extract_min()  // root of Huffman tree"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        text = params.get("text", "").strip()
        if not text:
            return

        # Count character frequencies
        freq: dict[str, int] = {}
        for ch in text:
            freq[ch] = freq.get(ch, 0) + 1

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Text: '{text}' ({len(text)} chars, {len(freq)} unique)",
            phase="init",
        )

        # Create leaf nodes for each character
        node_counter = 0
        heap = []  # (frequency, unique_id, node_data)
        node_map = {}  # id -> {"char": str, "freq": int, "left": id|None, "right": id|None}

        for ch, f in sorted(freq.items(), key=lambda x: x[1]):
            node_counter += 1
            nid = f"h{node_counter}"
            display = ch if ch != ' ' else '␣'
            node_map[nid] = {"char": display, "freq": f, "left": None, "right": None}

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=nid,
                value={"id": nid, "label": f"{display}:{f}"},
                message=f"Leaf: '{display}' appears {f} time(s)",
                phase="explore",
            )

            heapq.heappush(heap, (f, node_counter, nid))

        # Build Huffman tree by merging
        while len(heap) > 1:
            f1, _, left_id = heapq.heappop(heap)
            f2, _, right_id = heapq.heappop(heap)

            node_counter += 1
            parent_id = f"h{node_counter}"
            merged_freq = f1 + f2
            node_map[parent_id] = {"char": None, "freq": merged_freq, "left": left_id, "right": right_id}

            yield Step(
                action=StepAction.ADD_NODE,
                target_type="node",
                target_id=parent_id,
                value={"id": parent_id, "label": str(merged_freq)},
                message=f"Merge ({f1} + {f2} = {merged_freq})",
                phase="explore",
            )

            yield Step(
                action=StepAction.ADD_EDGE,
                target_type="edge",
                target_id=f"{parent_id}-{left_id}",
                value={"source": parent_id, "target": left_id, "label": "0"},
                message=f"Left edge: 0",
                phase="explore",
            )

            yield Step(
                action=StepAction.ADD_EDGE,
                target_type="edge",
                target_id=f"{parent_id}-{right_id}",
                value={"source": parent_id, "target": right_id, "label": "1"},
                message=f"Right edge: 1",
                phase="explore",
            )

            heapq.heappush(heap, (merged_freq, node_counter, parent_id))

        # Highlight the root
        if heap:
            _, _, root_id = heap[0]
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=root_id,
                value="path",
                message=f"Huffman tree root (total frequency: {node_map[root_id]['freq']})",
                phase="finalize",
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Huffman tree complete. {len(freq)} unique characters encoded.",
            phase="result",
        )

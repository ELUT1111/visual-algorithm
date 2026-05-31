"""Trie (Prefix Tree) - insert and search."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry


@registry.register
class TrieAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="trie",
            category="tree",
            description="Prefix tree for efficient string operations",
            emoji="📚",
            parameters=[
                {"name": "words", "type": "str", "required": True,
                 "description": "Comma-separated words to insert (e.g. cat,car,dog,do)"},
            ],
            time_complexity="O(m) per operation, m = word length",
            space_complexity="O(ALPHABET_SIZE * m * n)",
            layout="hierarchical",
            builds_structure=True,
            use_cases=[
                "Autocomplete / predictive text",
                "Spell checking",
                "IP routing tables",
                "Word games (Boggle, Scrabble)",
                "Prefix matching",
            ],
            pseudocode=(
                "function Trie_Insert(root, word):\n"
                "    node = root\n"
                "    for char in word:\n"
                "        if char not in node.children:\n"
                "            node.children[char] = new Node(char)\n"
                "        node = node.children[char]\n"
                "    node.is_end = true"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        words_str = params.get("words", "")
        if not words_str:
            return

        words = [w.strip().lower() for w in words_str.split(",") if w.strip()]
        if not words:
            return

        # Internal trie structure
        # Each node: {"id": str, "char": str, "children": {char: node_id}, "is_end": bool}
        trie_nodes: dict[str, dict] = {}
        node_counter = 0

        def make_node(char: str, is_root: bool = False) -> str:
            nonlocal node_counter
            node_counter += 1
            nid = f"t{node_counter}"
            trie_nodes[nid] = {"id": nid, "char": char, "children": {}, "is_end": False}
            return nid

        # Create root node
        root_id = make_node("*")
        yield Step(
            action=StepAction.ADD_NODE,
            target_type="node",
            target_id=root_id,
            value={"id": root_id, "label": "(root)"},
            message="Created trie root",
            phase="init",
        )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Inserting words: {', '.join(words)}",
            phase="init",
        )

        for word in words:
            current_id = root_id
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current_id,
                value="current",
                message=f"Inserting '{word}'",
                phase="explore",
            )

            for i, char in enumerate(word):
                children = trie_nodes[current_id]["children"]

                if char in children:
                    # Follow existing path
                    next_id = children[char]
                    edge_id = f"{current_id}-{next_id}"
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=edge_id,
                        value="exploring",
                        message=f"Follow existing edge '{char}'",
                        phase="explore",
                    )
                    yield Step(
                        action=StepAction.SET_NODE_COLOR,
                        target_type="node",
                        target_id=next_id,
                        value="current",
                        message=f"At node '{char}'",
                        phase="explore",
                    )
                else:
                    # Create new node
                    new_id = make_node(char)
                    trie_nodes[current_id]["children"][char] = new_id

                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=new_id,
                        value={"id": new_id, "label": char},
                        message=f"Create new node for '{char}'",
                        phase="explore",
                    )

                    edge_label = f"{current_id}-{new_id}"
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=edge_label,
                        value={"source": current_id, "target": new_id, "label": char},
                        message=f"Add edge '{char}'",
                        phase="explore",
                    )

                    next_id = new_id

                current_id = next_id

            # Mark end of word
            trie_nodes[current_id]["is_end"] = True
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current_id,
                value="path",
                message=f"'{word}' inserted (end marker)",
                phase="finalize",
            )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Trie construction complete. {len(words)} words inserted.",
            phase="result",
        )

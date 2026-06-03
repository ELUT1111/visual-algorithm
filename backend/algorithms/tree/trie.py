"""Trie with insertion, prefix counts, prefix query, and deletion."""
from __future__ import annotations

from typing import Generator

from backend.engine.protocol import AlgorithmMeta, AlgorithmProtocol, Step, StepAction
from backend.engine.registry import registry


@registry.register
class TrieAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="trie",
            category="tree",
            description="Prefix tree with word frequency, prefix counts, prefix query, and deletion",
            emoji="TR",
            parameters=[
                {"name": "words", "type": "str", "required": True, "description": "Comma-separated words to insert"},
                {
                    "name": "query_prefix",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "Optional prefix to query after insertion",
                },
                {
                    "name": "delete_words",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "Optional comma-separated words to delete",
                },
            ],
            time_complexity="O(m) per insert, delete, or prefix query",
            space_complexity="O(total inserted characters)",
            layout="hierarchical",
            builds_structure=True,
            use_cases=[
                "Autocomplete and predictive text",
                "Prefix frequency queries",
                "Spell checking dictionaries",
                "Word games",
                "Mutable dictionaries with deletion",
            ],
            pseudocode=(
                "insert(word):\n"
                "    node = root; node.prefix_count += 1\n"
                "    for char in word:\n"
                "        create child if missing\n"
                "        node = child; node.prefix_count += 1\n"
                "    node.word_count += 1\n"
                "\n"
                "delete(word):\n"
                "    follow path; if word_count is 0, stop\n"
                "    decrement word_count and prefix_count along path\n"
                "    prune nodes with prefix_count 0\n"
                "\n"
                "prefix_count(prefix): follow prefix path and return node.prefix_count"
            ),
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        raw_words = str(params.get("words", "") or "")
        words = [word.strip().lower() for word in raw_words.split(",") if word.strip()]
        if not words:
            return

        query_prefix = str(params.get("query_prefix", "") or "").strip().lower()
        delete_words = [
            word.strip().lower()
            for word in str(params.get("delete_words", "") or "").split(",")
            if word.strip()
        ]

        trie_nodes: dict[str, dict] = {}
        node_counter = 0

        def make_node(char: str, parent: str | None = None, edge_char: str = "") -> str:
            nonlocal node_counter
            node_counter += 1
            node_id = f"t{node_counter}"
            trie_nodes[node_id] = {
                "id": node_id,
                "char": char,
                "children": {},
                "is_end": False,
                "word_count": 0,
                "prefix_count": 0,
                "parent": parent,
                "edge_char": edge_char,
            }
            return node_id

        root_id = make_node("*")
        inserted_words: list[str] = []
        deleted_words: list[str] = []
        deletion_results: list[dict] = []
        prefix_query_result: dict | None = None

        def node_rows() -> dict[str, dict]:
            return {
                node_id: {
                    "char": node["char"],
                    "children": dict(sorted(node["children"].items())),
                    "is_end": node["is_end"],
                    "word_count": node["word_count"],
                    "prefix_count": node["prefix_count"],
                    "parent": node["parent"],
                    "edge_char": node["edge_char"],
                }
                for node_id, node in trie_nodes.items()
            }

        def word_frequency() -> dict[str, int]:
            frequencies: dict[str, int] = {}

            def collect(node_id: str, prefix: str) -> None:
                node = trie_nodes[node_id]
                if node["word_count"] > 0:
                    frequencies[prefix] = node["word_count"]
                for char, child_id in sorted(node["children"].items()):
                    collect(child_id, prefix + char)

            collect(root_id, "")
            return frequencies

        def state(extra: dict | None = None) -> dict:
            payload = {
                "root": root_id,
                "inserted_words": list(inserted_words),
                "deleted_words": list(deleted_words),
                "delete_words": list(delete_words),
                "query_prefix": query_prefix,
                "word_frequency": word_frequency(),
                "node_count": len(trie_nodes),
                "trie_nodes": node_rows(),
                "deletion_results": list(deletion_results),
                "prefix_query_result": prefix_query_result,
            }
            if extra:
                payload.update(extra)
            return payload

        yield Step(
            action=StepAction.ADD_NODE,
            target_type="node",
            target_id=root_id,
            value={"id": root_id, "label": "(root)"},
            message="Created trie root",
            phase="init",
            state=state({"current_node": root_id}),
        )
        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Inserting words: {', '.join(words)}",
            phase="init",
            state=state(),
        )

        for word in words:
            current = root_id
            path = [root_id]
            trie_nodes[current]["prefix_count"] += 1
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="current",
                message=f"Insert '{word}': increment root prefix count to {trie_nodes[current]['prefix_count']}",
                phase="explore",
                state=state({"current_word": word, "path": list(path), "current_node": current}),
            )

            for char in word:
                children = trie_nodes[current]["children"]
                if char in children:
                    child = children[char]
                    yield Step(
                        action=StepAction.HIGHLIGHT_EDGE,
                        target_type="edge",
                        target_id=f"{current}-{child}",
                        value="exploring",
                        message=f"Follow existing edge '{char}'",
                        phase="explore",
                        state=state({"current_word": word, "path": list(path), "current_node": child}),
                    )
                else:
                    child = make_node(char, current, char)
                    children[char] = child
                    yield Step(
                        action=StepAction.ADD_NODE,
                        target_type="node",
                        target_id=child,
                        value={"id": child, "label": char},
                        message=f"Create node for '{char}'",
                        phase="explore",
                        state=state({"current_word": word, "path": list(path), "current_node": child}),
                    )
                    yield Step(
                        action=StepAction.ADD_EDGE,
                        target_type="edge",
                        target_id=f"{current}-{child}",
                        value={"source": current, "target": child, "label": char},
                        message=f"Add edge '{char}'",
                        phase="explore",
                        state=state({"current_word": word, "path": list(path), "current_node": child}),
                    )

                current = child
                path.append(current)
                trie_nodes[current]["prefix_count"] += 1
                yield Step(
                    action=StepAction.UPDATE_NODE_LABEL,
                    target_type="node",
                    target_id=current,
                    value=f"{trie_nodes[current]['char']}\np={trie_nodes[current]['prefix_count']} w={trie_nodes[current]['word_count']}",
                    message=f"prefix_count({current}) = {trie_nodes[current]['prefix_count']}",
                    phase="explore",
                    state=state({"current_word": word, "path": list(path), "current_node": current}),
                )

            trie_nodes[current]["word_count"] += 1
            trie_nodes[current]["is_end"] = trie_nodes[current]["word_count"] > 0
            inserted_words.append(word)
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=current,
                value="path",
                message=f"'{word}' inserted; word_count = {trie_nodes[current]['word_count']}",
                phase="finalize",
                state=state({"current_word": word, "path": list(path), "terminal_node": current}),
            )

        if query_prefix:
            current = root_id
            path = [root_id]
            found = True
            for char in query_prefix:
                if char not in trie_nodes[current]["children"]:
                    found = False
                    break
                child = trie_nodes[current]["children"][char]
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=f"{current}-{child}",
                    value="exploring",
                    message=f"Prefix query follows '{char}'",
                    phase="explore",
                    state=state({"query_prefix": query_prefix, "prefix_path": list(path), "current_node": child}),
                )
                current = child
                path.append(current)

            prefix_query_result = {
                "prefix": query_prefix,
                "found": found,
                "count": trie_nodes[current]["prefix_count"] if found else 0,
                "node": current if found else None,
                "path": list(path) if found else list(path),
            }
            yield Step(
                action=StepAction.SET_NODE_COLOR if found else StepAction.ADD_MESSAGE,
                target_type="node",
                target_id=current if found else "",
                value="path" if found else None,
                message=(
                    f"Prefix '{query_prefix}' appears in {prefix_query_result['count']} inserted word(s)"
                    if found
                    else f"Prefix '{query_prefix}' is not present"
                ),
                phase="finalize",
                state=state({"prefix_query_result": prefix_query_result, "prefix_path": list(path)}),
            )

        def find_path(word: str) -> tuple[bool, list[str]]:
            current_id = root_id
            path_ids = [root_id]
            for char in word:
                if char not in trie_nodes[current_id]["children"]:
                    return False, path_ids
                current_id = trie_nodes[current_id]["children"][char]
                path_ids.append(current_id)
            return trie_nodes[current_id]["word_count"] > 0, path_ids

        for word in delete_words:
            exists, path = find_path(word)
            if not exists:
                deletion_results.append({"word": word, "deleted": False, "reason": "not found", "path": list(path)})
                yield Step(
                    action=StepAction.ADD_MESSAGE,
                    target_type="node",
                    target_id="",
                    message=f"Delete '{word}': word not found",
                    phase="explore",
                    state=state({"delete_word": word, "delete_path": list(path)}),
                )
                continue

            terminal = path[-1]
            trie_nodes[terminal]["word_count"] -= 1
            trie_nodes[terminal]["is_end"] = trie_nodes[terminal]["word_count"] > 0
            for node_id in path:
                trie_nodes[node_id]["prefix_count"] -= 1
            deleted_words.append(word)

            pruned: list[str] = []
            for node_id in reversed(path[1:]):
                node = trie_nodes[node_id]
                if node["prefix_count"] > 0 or node["word_count"] > 0 or node["children"]:
                    break
                parent_id = node["parent"]
                edge_char = node["edge_char"]
                if parent_id is not None and edge_char in trie_nodes[parent_id]["children"]:
                    del trie_nodes[parent_id]["children"][edge_char]
                pruned.append(node_id)
                yield Step(
                    action=StepAction.REMOVE_NODE,
                    target_type="node",
                    target_id=node_id,
                    message=f"Prune unused node '{node['char']}' after deleting '{word}'",
                    phase="finalize",
                    state=state({"delete_word": word, "delete_path": list(path), "pruned_nodes": list(pruned)}),
                )
                del trie_nodes[node_id]

            deletion_results.append({"word": word, "deleted": True, "path": list(path), "pruned_nodes": list(pruned)})
            yield Step(
                action=StepAction.SET_NODE_COLOR,
                target_type="node",
                target_id=terminal if terminal in trie_nodes else path[0],
                value="visited",
                message=f"Deleted '{word}'; updated prefix counts and pruned {len(pruned)} node(s)",
                phase="finalize",
                state=state({"delete_word": word, "delete_path": list(path), "pruned_nodes": list(pruned)}),
            )

        if query_prefix and delete_words:
            current = root_id
            path = [root_id]
            found = True
            for char in query_prefix:
                if char not in trie_nodes[current]["children"]:
                    found = False
                    break
                current = trie_nodes[current]["children"][char]
                path.append(current)
            prefix_query_result = {
                "prefix": query_prefix,
                "found": found,
                "count": trie_nodes[current]["prefix_count"] if found else 0,
                "node": current if found else None,
                "path": list(path),
                "after_deletion": True,
            }

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Trie complete. {sum(word_frequency().values())} word instance(s) remain.",
            phase="result",
            state=state({"remaining_word_count": sum(word_frequency().values())}),
        )

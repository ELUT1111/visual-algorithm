from __future__ import annotations

import unittest

from backend.engine.registry import registry
from backend.models.graph import Graph
from backend.routers.ws_algorithm import _is_dag


def make_graph(*, directed: bool, nodes: list[str], edges: list[tuple[str, str, float]]):
    return Graph(
        directed=directed,
        nodes=[{"id": node_id, "label": node_id} for node_id in nodes],
        edges=[
            {
                "id": f"{source}-{target}",
                "source": source,
                "target": target,
                "weight": weight,
                "label": str(weight),
                "directed": directed,
            }
            for source, target, weight in edges
        ],
    )


class AlgorithmRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.discover()

    def test_recommended_graph_algorithms_are_registered(self):
        keys = set(registry.list_keys())
        self.assertIn("graph/topological_sort", keys)
        self.assertIn("graph/cycle_detection", keys)
        self.assertIn("graph/connected_components", keys)
        self.assertIn("graph/tarjan_scc", keys)
        self.assertGreaterEqual(len(keys), 23)

    def test_metadata_separates_layout_from_structure_building(self):
        bst = registry.get("tree/bst").get_meta()
        tree_bfs = registry.get("tree/tree_bfs").get_meta()

        self.assertEqual(bst.layout, "hierarchical")
        self.assertTrue(bst.builds_structure)
        self.assertEqual(tree_bfs.layout, "hierarchical")
        self.assertFalse(tree_bfs.builds_structure)

    def test_negative_weight_metadata_for_dijkstra(self):
        dijkstra = registry.get("graph/dijkstra").get_meta()
        bellman_ford = registry.get("graph/bellman_ford").get_meta()

        self.assertFalse(dijkstra.allows_negative_weights)
        self.assertTrue(bellman_ford.allows_negative_weights)


class NewGraphAlgorithmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.discover()

    def test_topological_sort_emits_expected_order(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C"],
            edges=[("S", "A", 1), ("S", "B", 1), ("A", "C", 1), ("B", "C", 1)],
        )

        steps = list(registry.get("graph/topological_sort").run(graph, {}))
        messages = [step.message for step in steps]

        self.assertTrue(_is_dag(graph))
        self.assertIn("Topological order: S -> A -> B -> C", messages)
        self.assertTrue(any(step.state and "indegree" in step.state for step in steps))

    def test_cycle_detection_finds_directed_cycle(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C"],
            edges=[("A", "B", 1), ("B", "C", 1), ("C", "A", 1)],
        )

        steps = list(registry.get("graph/cycle_detection").run(graph, {}))

        self.assertFalse(_is_dag(graph))
        self.assertTrue(any("cycle found" in step.message for step in steps))
        self.assertTrue(any(step.state and step.state.get("cycle") for step in steps))

    def test_connected_components_finds_two_components(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D"],
            edges=[("A", "B", 1), ("C", "D", 1)],
        )

        steps = list(registry.get("graph/connected_components").run(graph, {}))

        self.assertTrue(any("Found 2 connected component(s)" == step.message for step in steps))
        result_state = steps[-1].state or {}
        self.assertEqual(len(result_state.get("components", [])), 2)

    def test_tarjan_scc_finds_strong_components(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C", "D"],
            edges=[("A", "B", 1), ("B", "A", 1), ("B", "C", 1), ("C", "D", 1), ("D", "C", 1)],
        )

        steps = list(registry.get("graph/tarjan_scc").run(graph, {}))
        components = steps[-1].state.get("components", [])

        self.assertEqual(len(components), 2)
        self.assertTrue(any(set(component) == {"A", "B"} for component in components))
        self.assertTrue(any(set(component) == {"C", "D"} for component in components))


if __name__ == "__main__":
    unittest.main()

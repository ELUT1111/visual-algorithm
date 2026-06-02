from __future__ import annotations

import unittest

from backend.engine.registry import registry
from backend.app import _build_health_payload
from backend.models.graph import Graph
from backend.routers.algorithms import compare_algorithms, CompareAlgorithmsRequest
from backend.routers.ws_algorithm import _is_dag, _validate_runner_inputs


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
        self.assertIn("graph/union_find", keys)
        self.assertIn("graph/bipartite", keys)
        self.assertIn("graph/floyd_warshall", keys)
        self.assertIn("graph/bridges_articulation", keys)
        self.assertIn("graph/kosaraju_scc", keys)
        self.assertIn("graph/spfa", keys)
        self.assertIn("graph/johnson", keys)
        self.assertIn("graph/edmonds_karp", keys)
        self.assertIn("graph/dinic", keys)
        self.assertIn("array/bubble_sort", keys)
        self.assertIn("array/quick_sort", keys)
        self.assertIn("array/merge_sort", keys)
        self.assertIn("array/heap_sort", keys)
        self.assertIn("array/binary_search", keys)
        self.assertIn("array/kadane", keys)
        self.assertIn("dp/lcs", keys)
        self.assertIn("dp/edit_distance", keys)
        self.assertIn("dp/knapsack", keys)
        self.assertIn("dp/lis", keys)
        self.assertIn("dp/coin_change", keys)
        self.assertIn("dp/matrix_chain_multiplication", keys)
        self.assertIn("dp/fibonacci_dp", keys)
        self.assertIn("dp/subset_sum", keys)
        self.assertIn("dp/word_break", keys)
        self.assertIn("string/kmp", keys)
        self.assertIn("string/rabin_karp", keys)
        self.assertIn("string/boyer_moore", keys)
        self.assertIn("string/z_algorithm", keys)
        self.assertIn("string/manacher", keys)
        self.assertIn("tree/fenwick_tree", keys)
        self.assertGreaterEqual(len(keys), 53)

    def test_health_payload_reports_algorithm_summary(self):
        payload = _build_health_payload()

        self.assertEqual(payload["status"], "ok")
        self.assertGreaterEqual(payload["algorithm_count"], 53)
        self.assertEqual(payload["categories"].get("graph"), 20)
        self.assertEqual(payload["categories"].get("tree"), 13)
        self.assertEqual(payload["categories"].get("array"), 6)
        self.assertEqual(payload["categories"].get("dp"), 9)
        self.assertEqual(payload["categories"].get("string"), 5)
        self.assertGreaterEqual(payload["visualizations"].get("graph", 0), 1)
        self.assertGreaterEqual(payload["visualizations"].get("array", 0), 1)
        self.assertGreaterEqual(payload["visualizations"].get("matrix", 0), 1)

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

    def test_undirected_metadata_for_low_link_algorithms(self):
        union_find = registry.get("graph/union_find").get_meta()
        bipartite = registry.get("graph/bipartite").get_meta()
        bridges = registry.get("graph/bridges_articulation").get_meta()
        prim = registry.get("graph/prim").get_meta()
        kruskal = registry.get("graph/kruskal").get_meta()

        self.assertTrue(union_find.requires_undirected)
        self.assertTrue(bipartite.requires_undirected)
        self.assertTrue(bridges.requires_undirected)
        self.assertTrue(prim.requires_undirected)
        self.assertTrue(kruskal.requires_undirected)

    def test_array_and_matrix_algorithms_do_not_require_graph(self):
        bubble_sort = registry.get("array/bubble_sort").get_meta()
        quick_sort = registry.get("array/quick_sort").get_meta()
        kadane = registry.get("array/kadane").get_meta()
        lcs = registry.get("dp/lcs").get_meta()
        edit_distance = registry.get("dp/edit_distance").get_meta()
        coin_change = registry.get("dp/coin_change").get_meta()
        matrix_chain = registry.get("dp/matrix_chain_multiplication").get_meta()
        fibonacci = registry.get("dp/fibonacci_dp").get_meta()
        subset_sum = registry.get("dp/subset_sum").get_meta()
        word_break = registry.get("dp/word_break").get_meta()
        kmp = registry.get("string/kmp").get_meta()
        manacher = registry.get("string/manacher").get_meta()
        fenwick = registry.get("tree/fenwick_tree").get_meta()

        self.assertFalse(bubble_sort.requires_graph)
        self.assertEqual(bubble_sort.visualization, "array")
        self.assertFalse(quick_sort.requires_graph)
        self.assertEqual(quick_sort.visualization, "array")
        self.assertFalse(kadane.requires_graph)
        self.assertEqual(kadane.visualization, "array")
        self.assertFalse(lcs.requires_graph)
        self.assertEqual(lcs.visualization, "matrix")
        self.assertFalse(edit_distance.requires_graph)
        self.assertEqual(edit_distance.visualization, "matrix")
        self.assertFalse(coin_change.requires_graph)
        self.assertEqual(coin_change.visualization, "array")
        self.assertFalse(matrix_chain.requires_graph)
        self.assertEqual(matrix_chain.visualization, "matrix")
        self.assertFalse(fibonacci.requires_graph)
        self.assertEqual(fibonacci.visualization, "array")
        self.assertFalse(subset_sum.requires_graph)
        self.assertEqual(subset_sum.visualization, "matrix")
        self.assertFalse(word_break.requires_graph)
        self.assertEqual(word_break.visualization, "array")
        self.assertFalse(kmp.requires_graph)
        self.assertEqual(kmp.visualization, "array")
        self.assertFalse(manacher.requires_graph)
        self.assertEqual(manacher.visualization, "array")
        self.assertFalse(fenwick.requires_graph)
        self.assertEqual(fenwick.visualization, "array")

    def test_preflight_rejects_dijkstra_negative_edges(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B"],
            edges=[("A", "B", -1)],
        )
        meta = registry.get("graph/dijkstra").get_meta()

        with self.assertRaisesRegex(ValueError, "negative edge weights"):
            _validate_runner_inputs("graph/dijkstra", meta, graph, {"source": "A"})

    def test_preflight_rejects_flow_same_source_and_target(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "T"],
            edges=[("S", "T", 5)],
        )
        meta = registry.get("graph/edmonds_karp").get_meta()

        with self.assertRaisesRegex(ValueError, "source and target"):
            _validate_runner_inputs("graph/edmonds_karp", meta, graph, {"source": "S", "target": "S"})

    def test_preflight_rejects_flow_non_positive_capacity(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "T"],
            edges=[("S", "T", 0)],
        )
        meta = registry.get("graph/dinic").get_meta()

        with self.assertRaisesRegex(ValueError, "positive capacities"):
            _validate_runner_inputs("graph/dinic", meta, graph, {"source": "S", "target": "T"})

    def test_preflight_rejects_mst_on_directed_graph(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B"],
            edges=[("A", "B", 1)],
        )
        meta = registry.get("graph/prim").get_meta()

        with self.assertRaisesRegex(ValueError, "undirected graph"):
            _validate_runner_inputs("graph/prim", meta, graph, {"source": "A"})

    def test_preflight_rejects_johnson_negative_cycle(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B"],
            edges=[("A", "B", -2), ("B", "A", -2)],
        )
        meta = registry.get("graph/johnson").get_meta()

        with self.assertRaisesRegex(ValueError, "negative-weight cycles"):
            _validate_runner_inputs("graph/johnson", meta, graph, {})

    def test_preflight_rejects_spfa_reachable_negative_cycle(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B"],
            edges=[("S", "A", 1), ("A", "B", -2), ("B", "A", -2)],
        )
        meta = registry.get("graph/spfa").get_meta()

        with self.assertRaisesRegex(ValueError, "negative-weight cycle"):
            _validate_runner_inputs("graph/spfa", meta, graph, {"source": "S"})

    def test_compare_endpoint_summarizes_max_flow_algorithms(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C", "D", "T"],
            edges=[
                ("S", "A", 16),
                ("S", "C", 13),
                ("A", "B", 12),
                ("B", "C", 9),
                ("C", "A", 4),
                ("C", "D", 14),
                ("D", "B", 7),
                ("B", "T", 20),
                ("D", "T", 4),
            ],
        )

        response = compare_algorithms(
            CompareAlgorithmsRequest(
                algorithm_keys=["graph/edmonds_karp", "graph/dinic"],
                graph=graph.model_dump(),
                params={"source": "S", "target": "T"},
            )
        )
        results = response["results"]

        self.assertEqual(response["algorithm_count"], 2)
        self.assertTrue(all(result["status"] == "ok" for result in results))
        self.assertEqual([result["summary"].get("max_flow") for result in results], [23, 23])
        self.assertTrue(all(result["step_count"] > 0 for result in results))


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

    def test_kosaraju_scc_finds_strong_components(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C", "D", "E"],
            edges=[
                ("A", "B", 1),
                ("B", "A", 1),
                ("B", "C", 1),
                ("C", "D", 1),
                ("D", "C", 1),
                ("D", "E", 1),
            ],
        )

        steps = list(registry.get("graph/kosaraju_scc").run(graph, {}))
        components = steps[-1].state.get("components", [])

        self.assertEqual(len(components), 3)
        self.assertTrue(any(set(component) == {"A", "B"} for component in components))
        self.assertTrue(any(set(component) == {"C", "D"} for component in components))
        self.assertTrue(any(set(component) == {"E"} for component in components))
        self.assertIn("finish_order", steps[-1].state)

    def test_union_find_finds_components(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D"],
            edges=[("A", "B", 1), ("C", "D", 1)],
        )

        steps = list(registry.get("graph/union_find").run(graph, {}))
        components = steps[-1].state.get("components", [])

        self.assertEqual(len(components), 2)
        self.assertTrue(any(set(component) == {"A", "B"} for component in components))
        self.assertTrue(any(set(component) == {"C", "D"} for component in components))

    def test_bipartite_detects_odd_cycle(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C"],
            edges=[("A", "B", 1), ("B", "C", 1), ("C", "A", 1)],
        )

        steps = list(registry.get("graph/bipartite").run(graph, {}))

        self.assertTrue(any("Conflict:" in step.message for step in steps))
        self.assertTrue(any(step.state and step.state.get("conflict") for step in steps))

    def test_floyd_warshall_updates_shortest_path(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C"],
            edges=[("A", "B", 3), ("B", "C", 2), ("A", "C", 10)],
        )

        steps = list(registry.get("graph/floyd_warshall").run(graph, {}))
        matrix = steps[-1].state["distance_matrix"]
        row_a = matrix["rows"].index("A")
        col_c = matrix["columns"].index("C")

        self.assertEqual(matrix["values"][row_a][col_c], 5)

    def test_bridges_articulation_finds_chain_middle(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C"],
            edges=[("A", "B", 1), ("B", "C", 1)],
        )

        steps = list(registry.get("graph/bridges_articulation").run(graph, {}))
        state = steps[-1].state

        self.assertIn("B", state.get("articulation_points", []))
        self.assertEqual(len(state.get("bridges", [])), 2)

    def test_spfa_handles_negative_edges_without_negative_cycle(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C", "T"],
            edges=[
                ("S", "A", 6),
                ("S", "B", 7),
                ("A", "C", 5),
                ("B", "A", -2),
                ("B", "C", 4),
                ("C", "T", -1),
            ],
        )

        steps = list(registry.get("graph/spfa").run(graph, {"source": "S"}))
        state = steps[-1].state

        self.assertFalse(state.get("negative_cycle"))
        self.assertEqual(state.get("distances", {}).get("T"), 9)

    def test_johnson_computes_all_pairs_shortest_paths(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C", "D"],
            edges=[("A", "B", 3), ("A", "C", 8), ("B", "C", -2), ("B", "D", 1), ("C", "D", 2)],
        )

        steps = list(registry.get("graph/johnson").run(graph, {}))
        matrix = steps[-1].state["distance_matrix"]
        row_a = matrix["rows"].index("A")
        col_c = matrix["columns"].index("C")
        col_d = matrix["columns"].index("D")

        self.assertEqual(matrix["values"][row_a][col_c], 1)
        self.assertEqual(matrix["values"][row_a][col_d], 3)

    def test_edmonds_karp_computes_max_flow(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C", "D", "T"],
            edges=[
                ("S", "A", 16),
                ("S", "C", 13),
                ("A", "B", 12),
                ("B", "C", 9),
                ("C", "A", 4),
                ("C", "D", 14),
                ("D", "B", 7),
                ("B", "T", 20),
                ("D", "T", 4),
            ],
        )

        steps = list(registry.get("graph/edmonds_karp").run(graph, {"source": "S", "target": "T"}))

        self.assertEqual(steps[-1].state.get("max_flow"), 23)
        self.assertIn("residual_network", steps[-1].state)
        self.assertIn("augmentations", steps[-1].state)
        augment_step = next(step for step in steps if step.state and step.state.get("augmenting_path_edges"))
        self.assertIn("bottleneck_edges", augment_step.state)
        self.assertTrue(augment_step.state.get("bottleneck_edges"))

    def test_dinic_computes_max_flow(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C", "D", "T"],
            edges=[
                ("S", "A", 16),
                ("S", "C", 13),
                ("A", "B", 12),
                ("B", "C", 9),
                ("C", "A", 4),
                ("C", "D", 14),
                ("D", "B", 7),
                ("B", "T", 20),
                ("D", "T", 4),
            ],
        )

        steps = list(registry.get("graph/dinic").run(graph, {"source": "S", "target": "T"}))

        self.assertEqual(steps[-1].state.get("max_flow"), 23)
        self.assertIn("residual_network", steps[-1].state)
        level_step = next(step for step in steps if step.state and step.state.get("level_graph_edges"))
        self.assertIn("levels", level_step.state)
        augment_step = next(step for step in steps if step.state and step.state.get("augmenting_path_edges"))
        self.assertIn("bottleneck_edges", augment_step.state)
        self.assertTrue(augment_step.state.get("bottleneck_edges"))

    def test_bubble_sort_sorts_array(self):
        steps = list(registry.get("array/bubble_sort").run(Graph(), {"values": "5,1,4,2"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("array"), [1, 2, 4, 5])
        self.assertTrue(steps[-1].state.get("sorted"))

    def test_bfs_reports_queue_and_visited_state(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C"],
            edges=[("A", "B", 1), ("B", "C", 1)],
        )

        steps = list(registry.get("graph/bfs").run(graph, {"source": "A", "target": "C"}))

        bfs_init = steps[0].state
        self.assertEqual(bfs_init.get("queue"), ["A"])
        self.assertEqual(bfs_init.get("visited"), ["A"])
        self.assertIn("parent", bfs_init)
        self.assertTrue(any(step.state and step.state.get("found") for step in steps))

    def test_dfs_reports_stack_and_visited_state(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C"],
            edges=[("A", "B", 1), ("B", "C", 1)],
        )

        steps = list(registry.get("graph/dfs").run(graph, {"source": "A", "target": "C"}))

        dfs_init = steps[0].state
        self.assertEqual(dfs_init.get("stack"), ["A"])
        self.assertEqual(dfs_init.get("visited"), ["A"])
        self.assertIn("parent", dfs_init)
        self.assertTrue(any(step.state and step.state.get("found") for step in steps))

    def test_dijkstra_reports_distance_table(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C"],
            edges=[("A", "B", 3), ("B", "C", 2), ("A", "C", 10)],
        )

        steps = list(registry.get("graph/dijkstra").run(graph, {"source": "A"}))
        init_state = steps[0].state

        self.assertEqual(init_state.get("distances", {}).get("A"), 0)
        self.assertEqual(init_state.get("distances", {}).get("B"), "∞")
        self.assertIn("queue", init_state)
        self.assertTrue(any(step.state and step.state.get("path_target") == "C" for step in steps))

    def test_bellman_ford_reports_iteration_and_relaxation_state(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C"],
            edges=[("S", "A", 4), ("A", "B", 2), ("S", "C", 10)],
        )

        steps = list(registry.get("graph/bellman_ford").run(graph, {"source": "S"}))
        iteration_step = next(step for step in steps if step.state and step.state.get("iteration") == 1)

        self.assertEqual(iteration_step.state.get("distances", {}).get("S"), 0)
        self.assertIn("previous", iteration_step.state)
        self.assertTrue(any(step.state and step.state.get("edge") for step in steps))

    def test_quick_sort_sorts_array(self):
        steps = list(registry.get("array/quick_sort").run(Graph(), {"values": "5,1,4,2"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("array"), [1, 2, 4, 5])
        self.assertTrue(steps[-1].state.get("sorted"))

    def test_merge_sort_sorts_array(self):
        steps = list(registry.get("array/merge_sort").run(Graph(), {"values": "5,1,4,2"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("array"), [1, 2, 4, 5])
        self.assertTrue(steps[-1].state.get("sorted"))

    def test_heap_sort_sorts_array(self):
        steps = list(registry.get("array/heap_sort").run(Graph(), {"values": "5,1,4,2"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("array"), [1, 2, 4, 5])
        self.assertTrue(steps[-1].state.get("sorted"))

    def test_binary_search_finds_target(self):
        steps = list(registry.get("array/binary_search").run(Graph(), {"values": "1,2,4,5", "target": "4"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertTrue(steps[-1].state.get("found"))
        self.assertEqual(steps[-1].state.get("index"), 2)

    def test_kadane_finds_maximum_subarray(self):
        steps = list(registry.get("array/kadane").run(Graph(), {"values": "-2,1,-3,4,-1,2,1,-5,4"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertIn("trace", steps[-1].state)
        self.assertIn("best_window", steps[-1].state)
        self.assertEqual(steps[-1].state.get("max_sum"), 6)
        self.assertEqual(steps[-1].state.get("subarray"), [4, -1, 2, 1])

    def test_lcs_computes_dynamic_programming_matrix(self):
        steps = list(registry.get("dp/lcs").run(Graph(), {"text_a": "abcde", "text_b": "ace"}))

        self.assertEqual(steps[0].action.value, "render_matrix")
        self.assertEqual(steps[-1].state.get("lcs"), "ace")
        self.assertEqual(steps[-1].state.get("length"), 3)
        self.assertIn("backtrack_path", steps[-1].state)
        self.assertIn("path_cells", steps[-1].state)

    def test_edit_distance_computes_distance(self):
        steps = list(registry.get("dp/edit_distance").run(Graph(), {"text_a": "kitten", "text_b": "sitting"}))

        self.assertEqual(steps[0].action.value, "render_matrix")
        self.assertEqual(steps[-1].state.get("distance"), 3)
        self.assertIn("edit_script", steps[-1].state)
        self.assertIn("backtrack_path", steps[-1].state)

    def test_knapsack_computes_max_value(self):
        steps = list(
            registry.get("dp/knapsack").run(
                Graph(),
                {"weights": "2,3,4", "values": "3,4,5", "capacity": "5"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_matrix")
        self.assertEqual(steps[-1].state.get("max_value"), 7)
        self.assertEqual(steps[-1].state.get("selected_indices"), [0, 1])
        self.assertEqual(steps[-1].state.get("total_weight"), 5)
        self.assertIn("selected_items", steps[-1].state)
        self.assertIn("backtrack_path", steps[-1].state)

    def test_coin_change_computes_minimum_coins(self):
        steps = list(
            registry.get("dp/coin_change").run(
                Graph(),
                {"coins": "1,2,5", "amount": "11"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertIn("dp_table", steps[-1].state)
        self.assertIn("combination_steps", steps[-1].state)
        self.assertEqual(steps[-1].state.get("min_coins"), 3)
        self.assertEqual(sorted(steps[-1].state.get("combination")), [1, 5, 5])

    def test_lis_computes_longest_increasing_subsequence(self):
        steps = list(
            registry.get("dp/lis").run(Graph(), {"values": "10,9,2,5,3,7,101,18"})
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("length"), 4)
        self.assertEqual(steps[-1].state.get("sequence"), [2, 5, 7, 101])

    def test_matrix_chain_computes_minimum_cost(self):
        steps = list(
            registry.get("dp/matrix_chain_multiplication").run(
                Graph(),
                {"dimensions": "30,35,15,5,10,20,25"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_matrix")
        self.assertEqual(steps[-1].state.get("min_cost"), 15125)
        self.assertIn("parenthesization", steps[-1].state)
        self.assertIn("parenthesization_tree", steps[-1].state)
        self.assertIn("split_trace", steps[-1].state)

    def test_fibonacci_dp_computes_sequence(self):
        steps = list(registry.get("dp/fibonacci_dp").run(Graph(), {"n": "10"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("fib_n"), 55)

    def test_subset_sum_finds_target_subset(self):
        values = [3, 34, 4, 12, 5, 2]
        steps = list(
            registry.get("dp/subset_sum").run(
                Graph(),
                {"values": ",".join(str(value) for value in values), "target": "9"},
            )
        )
        selected = steps[-1].state.get("selected_indices")

        self.assertEqual(steps[0].action.value, "render_matrix")
        self.assertTrue(steps[-1].state.get("subset_found"))
        self.assertEqual(sum(values[idx] for idx in selected), 9)
        self.assertEqual(steps[-1].state.get("selected_sum"), 9)
        self.assertIn("selected_values", steps[-1].state)
        self.assertIn("backtrack_path", steps[-1].state)

    def test_word_break_finds_segmentation(self):
        steps = list(
            registry.get("dp/word_break").run(
                Graph(),
                {"text": "catsanddog", "words": "cat,cats,and,sand,dog"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertTrue(steps[-1].state.get("can_segment"))
        self.assertEqual(steps[-1].state.get("segmentation"), ["cat", "sand", "dog"])
        self.assertIn("dp_table", steps[-1].state)

    def test_fenwick_tree_computes_prefix_sum(self):
        steps = list(
            registry.get("tree/fenwick_tree").run(
                Graph(),
                {"values": "1,7,3,0,7,8,3,2,6,2", "query_index": "5"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("prefix_sum"), 18)
        self.assertEqual(steps[-1].state.get("query_path"), [5, 4])
        self.assertIn("tree", steps[-1].state)

    def test_kmp_finds_pattern_matches(self):
        steps = list(
            registry.get("string/kmp").run(
                Graph(),
                {"text": "abxabcabcaby", "pattern": "abcaby"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertIn("lps_table", steps[0].state)
        self.assertIn("lps_table", steps[-1].state)
        self.assertEqual(steps[-1].state.get("matches"), [6])

    def test_rabin_karp_finds_pattern_matches(self):
        steps = list(
            registry.get("string/rabin_karp").run(
                Graph(),
                {"text": "ababcabcabababd", "pattern": "ababd"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertIn("pattern_hash", steps[0].state)
        self.assertEqual(steps[-1].state.get("matches"), [10])

    def test_boyer_moore_finds_pattern_matches(self):
        steps = list(
            registry.get("string/boyer_moore").run(
                Graph(),
                {"text": "HERE IS A SIMPLE EXAMPLE", "pattern": "EXAMPLE"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertIn("bad_char_table", steps[0].state)
        self.assertEqual(steps[-1].state.get("matches"), [17])

    def test_z_algorithm_finds_pattern_matches(self):
        steps = list(
            registry.get("string/z_algorithm").run(
                Graph(),
                {"text": "aabxaabxcaabxaabxay", "pattern": "aabxa"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertIn("z_table", steps[0].state)
        self.assertEqual(steps[-1].state.get("matches"), [0, 9, 13])

    def test_manacher_finds_longest_palindrome(self):
        steps = list(registry.get("string/manacher").run(Graph(), {"text": "babad"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertIn(steps[-1].state.get("longest_palindrome"), {"bab", "aba"})
        self.assertEqual(steps[-1].state.get("length"), 3)
        self.assertIn("radii_table", steps[-1].state)


if __name__ == "__main__":
    unittest.main()

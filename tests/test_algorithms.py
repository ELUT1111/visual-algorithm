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
        self.assertIn("graph/dag_longest_path", keys)
        self.assertIn("graph/dominator_tree", keys)
        self.assertIn("graph/directed_mst", keys)
        self.assertIn("graph/yen_k_shortest_paths", keys)
        self.assertIn("graph/suurballe_disjoint_paths", keys)
        self.assertIn("graph/karp_minimum_mean_cycle", keys)
        self.assertIn("graph/minimum_cycle_basis", keys)
        self.assertIn("graph/euler_path", keys)
        self.assertIn("graph/edmonds_karp", keys)
        self.assertIn("graph/dinic", keys)
        self.assertIn("graph/push_relabel", keys)
        self.assertIn("graph/hopcroft_karp", keys)
        self.assertIn("graph/blossom_matching", keys)
        self.assertIn("graph/min_cost_max_flow", keys)
        self.assertIn("graph/stoer_wagner", keys)
        self.assertIn("graph/gomory_hu_tree", keys)
        self.assertIn("array/bubble_sort", keys)
        self.assertIn("array/quick_sort", keys)
        self.assertIn("array/merge_sort", keys)
        self.assertIn("array/heap_sort", keys)
        self.assertIn("array/binary_search", keys)
        self.assertIn("array/kadane", keys)
        self.assertIn("array/sparse_table", keys)
        self.assertIn("dp/lcs", keys)
        self.assertIn("dp/edit_distance", keys)
        self.assertIn("dp/knapsack", keys)
        self.assertIn("dp/lis", keys)
        self.assertIn("dp/coin_change", keys)
        self.assertIn("dp/matrix_chain_multiplication", keys)
        self.assertIn("dp/fibonacci_dp", keys)
        self.assertIn("dp/subset_sum", keys)
        self.assertIn("dp/word_break", keys)
        self.assertIn("dp/hungarian", keys)
        self.assertIn("string/kmp", keys)
        self.assertIn("string/rabin_karp", keys)
        self.assertIn("string/boyer_moore", keys)
        self.assertIn("string/z_algorithm", keys)
        self.assertIn("string/manacher", keys)
        self.assertIn("string/suffix_array", keys)
        self.assertIn("string/suffix_automaton", keys)
        self.assertIn("tree/fenwick_tree", keys)
        self.assertIn("tree/segment_tree", keys)
        self.assertIn("tree/treap", keys)
        self.assertIn("tree/lca", keys)
        self.assertIn("tree/heavy_light_decomposition", keys)
        self.assertGreaterEqual(len(keys), 75)

    def test_health_payload_reports_algorithm_summary(self):
        payload = _build_health_payload()

        self.assertEqual(payload["status"], "ok")
        self.assertGreaterEqual(payload["algorithm_count"], 75)
        self.assertEqual(payload["categories"].get("graph"), 34)
        self.assertEqual(payload["categories"].get("tree"), 17)
        self.assertEqual(payload["categories"].get("array"), 7)
        self.assertEqual(payload["categories"].get("dp"), 10)
        self.assertEqual(payload["categories"].get("string"), 7)
        self.assertGreaterEqual(payload["visualizations"].get("graph", 0), 1)
        self.assertGreaterEqual(payload["visualizations"].get("array", 0), 1)
        self.assertGreaterEqual(payload["visualizations"].get("matrix", 0), 1)

    def test_algorithm_metadata_includes_bilingual_education(self):
        metas = registry.list_all()

        self.assertGreaterEqual(len(metas), 75)
        for meta in metas:
            data = meta.to_dict()
            education = data.get("education", {})
            self.assertIn("en", education)
            self.assertIn("zh", education)
            self.assertTrue(education["en"].get("summary"))
            self.assertTrue(education["zh"].get("summary"))
            self.assertTrue(education["en"].get("idea"))
            self.assertTrue(education["zh"].get("idea"))
            self.assertIn("labels", education["en"])
            self.assertIn("labels", education["zh"])

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
        stoer_wagner = registry.get("graph/stoer_wagner").get_meta()
        gomory_hu = registry.get("graph/gomory_hu_tree").get_meta()
        prim = registry.get("graph/prim").get_meta()
        kruskal = registry.get("graph/kruskal").get_meta()

        self.assertTrue(union_find.requires_undirected)
        self.assertTrue(bipartite.requires_undirected)
        self.assertTrue(bridges.requires_undirected)
        self.assertTrue(stoer_wagner.requires_undirected)
        self.assertTrue(gomory_hu.requires_undirected)
        self.assertTrue(prim.requires_undirected)
        self.assertTrue(kruskal.requires_undirected)

    def test_array_and_matrix_algorithms_do_not_require_graph(self):
        bubble_sort = registry.get("array/bubble_sort").get_meta()
        quick_sort = registry.get("array/quick_sort").get_meta()
        kadane = registry.get("array/kadane").get_meta()
        sparse_table = registry.get("array/sparse_table").get_meta()
        lcs = registry.get("dp/lcs").get_meta()
        edit_distance = registry.get("dp/edit_distance").get_meta()
        coin_change = registry.get("dp/coin_change").get_meta()
        matrix_chain = registry.get("dp/matrix_chain_multiplication").get_meta()
        fibonacci = registry.get("dp/fibonacci_dp").get_meta()
        subset_sum = registry.get("dp/subset_sum").get_meta()
        word_break = registry.get("dp/word_break").get_meta()
        hungarian = registry.get("dp/hungarian").get_meta()
        kmp = registry.get("string/kmp").get_meta()
        manacher = registry.get("string/manacher").get_meta()
        suffix_array = registry.get("string/suffix_array").get_meta()
        suffix_automaton = registry.get("string/suffix_automaton").get_meta()
        fenwick = registry.get("tree/fenwick_tree").get_meta()
        segment_tree = registry.get("tree/segment_tree").get_meta()

        self.assertFalse(bubble_sort.requires_graph)
        self.assertEqual(bubble_sort.visualization, "array")
        self.assertFalse(quick_sort.requires_graph)
        self.assertEqual(quick_sort.visualization, "array")
        self.assertFalse(kadane.requires_graph)
        self.assertEqual(kadane.visualization, "array")
        self.assertFalse(sparse_table.requires_graph)
        self.assertEqual(sparse_table.visualization, "matrix")
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
        self.assertFalse(hungarian.requires_graph)
        self.assertEqual(hungarian.visualization, "matrix")
        self.assertFalse(kmp.requires_graph)
        self.assertEqual(kmp.visualization, "array")
        self.assertFalse(manacher.requires_graph)
        self.assertEqual(manacher.visualization, "array")
        self.assertFalse(suffix_array.requires_graph)
        self.assertEqual(suffix_array.visualization, "array")
        self.assertFalse(suffix_automaton.requires_graph)
        self.assertEqual(suffix_automaton.visualization, "graph")
        self.assertFalse(fenwick.requires_graph)
        self.assertEqual(fenwick.visualization, "array")
        self.assertFalse(segment_tree.requires_graph)
        self.assertEqual(segment_tree.visualization, "array")

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

    def test_dag_longest_path_finds_critical_path(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C", "D", "T"],
            edges=[
                ("S", "A", 4),
                ("S", "B", 2),
                ("A", "C", 3),
                ("A", "D", 7),
                ("B", "A", 1),
                ("B", "D", 5),
                ("C", "T", 2),
                ("D", "T", 3),
            ],
        )

        steps = list(registry.get("graph/dag_longest_path").run(graph, {"source": "S", "target": "T"}))
        state = steps[-1].state

        self.assertEqual(state.get("longest_distance"), 14)
        self.assertEqual(state.get("critical_path"), ["S", "A", "D", "T"])
        self.assertIn("topological_order", state)
        self.assertIn("distances", state)

    def test_dominator_tree_computes_immediate_dominators_and_frontiers(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C", "D", "E", "T"],
            edges=[
                ("S", "A", 1),
                ("S", "B", 1),
                ("A", "C", 1),
                ("B", "C", 1),
                ("C", "D", 1),
                ("C", "E", 1),
                ("D", "T", 1),
                ("E", "T", 1),
            ],
        )

        steps = list(registry.get("graph/dominator_tree").run(graph, {"source": "S"}))
        state = steps[-1].state

        self.assertEqual(state.get("source"), "S")
        self.assertEqual(
            state.get("immediate_dominators"),
            {"A": "S", "B": "S", "C": "S", "D": "C", "E": "C", "T": "C"},
        )
        self.assertEqual(state.get("dominators", {}).get("T"), ["S", "C", "T"])
        self.assertEqual(state.get("dominance_frontier", {}).get("A"), ["C"])
        self.assertEqual(state.get("dominance_frontier", {}).get("D"), ["T"])
        self.assertEqual(len(state.get("dominator_tree", [])), 6)

    def test_directed_mst_contracts_cycle_and_expands_arborescence(self):
        graph = make_graph(
            directed=True,
            nodes=["R", "A", "B", "C", "D"],
            edges=[
                ("R", "A", 4),
                ("R", "B", 6),
                ("R", "D", 10),
                ("A", "B", 1),
                ("B", "C", 1),
                ("C", "A", 1),
                ("C", "D", 1),
                ("A", "D", 4),
            ],
        )

        steps = list(registry.get("graph/directed_mst").run(graph, {"source": "R"}))
        state = steps[-1].state
        result_edges = {row["edge"] for row in state.get("arborescence_edges", [])}

        self.assertEqual(state.get("root"), "R")
        self.assertEqual(state.get("total_weight"), 7)
        self.assertEqual(result_edges, {"R-A", "A-B", "B-C", "C-D"})
        self.assertTrue(state.get("cycle_trace"))
        self.assertTrue(state.get("contractions"))

    def test_yen_k_shortest_paths_returns_ranked_alternatives(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C", "D", "T"],
            edges=[
                ("S", "A", 1),
                ("S", "B", 1),
                ("A", "C", 1),
                ("B", "C", 1),
                ("A", "D", 2),
                ("B", "D", 2),
                ("C", "T", 1),
                ("D", "T", 1),
                ("C", "D", 1),
            ],
        )

        steps = list(registry.get("graph/yen_k_shortest_paths").run(graph, {"source": "S", "target": "T", "k": 3}))
        state = steps[-1].state
        paths = state.get("shortest_paths", [])

        self.assertEqual([row["cost"] for row in paths], [3, 3, 4])
        self.assertEqual(paths[0]["path"], ["S", "A", "C", "T"])
        self.assertEqual(paths[1]["path"], ["S", "B", "C", "T"])
        self.assertEqual(len(paths), 3)
        self.assertTrue(state.get("spur_iterations"))

    def test_suurballe_disjoint_paths_finds_two_edge_disjoint_routes(self):
        graph = make_graph(
            directed=True,
            nodes=["S", "A", "B", "C", "D", "T"],
            edges=[
                ("S", "A", 1),
                ("A", "C", 1),
                ("C", "T", 1),
                ("S", "B", 1),
                ("B", "D", 1),
                ("D", "T", 1),
                ("A", "D", 3),
                ("B", "C", 3),
            ],
        )

        steps = list(registry.get("graph/suurballe_disjoint_paths").run(graph, {"source": "S", "target": "T"}))
        state = steps[-1].state
        paths = state.get("disjoint_paths", [])
        path_edges = {tuple(row["edges"]) for row in paths}

        self.assertEqual(state.get("total_cost"), 6)
        self.assertEqual(len(paths), 2)
        self.assertEqual(path_edges, {("S-A", "A-C", "C-T"), ("S-B", "B-D", "D-T")})
        self.assertIn("first_path", state)
        self.assertEqual(len(state.get("residual_augmentations", [])), 2)

    def test_karp_minimum_mean_cycle_finds_lowest_average_cycle(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C", "D"],
            edges=[
                ("A", "B", 4),
                ("B", "C", 4),
                ("C", "A", 4),
                ("C", "D", 1),
                ("D", "C", 1),
                ("A", "D", 6),
            ],
        )

        steps = list(registry.get("graph/karp_minimum_mean_cycle").run(graph, {}))
        state = steps[-1].state

        self.assertEqual(state.get("cycle_mean"), 1)
        self.assertEqual(state.get("minimum_mean_cycle"), ["C", "D", "C"])
        self.assertEqual(set(state.get("minimum_mean_cycle_edges", [])), {"C-D", "D-C"})
        self.assertIn("dp_table", state)
        self.assertTrue(state.get("mean_candidates"))

    def test_minimum_cycle_basis_selects_independent_light_cycles(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D"],
            edges=[
                ("A", "B", 1),
                ("B", "C", 1),
                ("C", "D", 1),
                ("D", "A", 1),
                ("A", "C", 1),
            ],
        )

        steps = list(registry.get("graph/minimum_cycle_basis").run(graph, {}))
        state = steps[-1].state
        basis = state.get("minimum_cycle_basis", [])
        basis_edges = {frozenset(row["edges"]) for row in basis}

        self.assertEqual(state.get("cycle_rank"), 2)
        self.assertEqual(state.get("total_weight"), 6)
        self.assertEqual(len(basis), 2)
        self.assertEqual(
            basis_edges,
            {frozenset({"A-B", "B-C", "A-C"}), frozenset({"D-A", "C-D", "A-C"})},
        )
        self.assertTrue(state.get("candidate_cycles"))
        self.assertTrue(state.get("selection_trace"))

    def test_euler_path_uses_every_edge_once(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D", "E"],
            edges=[
                ("A", "B", 1),
                ("B", "C", 1),
                ("C", "D", 1),
                ("D", "A", 1),
                ("A", "E", 1),
                ("E", "C", 1),
            ],
        )

        steps = list(registry.get("graph/euler_path").run(graph, {"start": "A"}))
        state = steps[-1].state

        self.assertTrue(state.get("is_eulerian"))
        self.assertEqual(state.get("mode"), "path")
        self.assertEqual(state.get("euler_path", [None])[0], "A")
        self.assertEqual(len(state.get("euler_path", [])), 7)
        self.assertEqual(len(state.get("euler_edges", [])), 6)
        self.assertEqual(state.get("used_edge_count"), state.get("edge_count"))

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
        self.assertIn("find_traces", steps[-1].state)
        self.assertIn("compression_updates", steps[-1].state)
        self.assertIn("union_trace", steps[-1].state)
        self.assertIn("rank_updates", steps[-1].state)
        self.assertGreaterEqual(len(steps[-1].state.get("rank_updates")), 2)

    def test_kruskal_reports_dsu_optimization_state(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D"],
            edges=[
                ("A", "B", 1),
                ("B", "C", 2),
                ("A", "C", 3),
                ("C", "D", 4),
            ],
        )

        steps = list(registry.get("graph/kruskal").run(graph, {}))
        state = steps[-1].state

        self.assertEqual(state.get("total_weight"), 7)
        self.assertEqual(len(state.get("mst_edges")), 3)
        self.assertIn("find_traces", state)
        self.assertIn("compression_updates", state)
        self.assertIn("union_trace", state)
        self.assertIn("rank_updates", state)
        self.assertTrue(state.get("union_trace"))

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
        self.assertEqual(len(state.get("biconnected_components", [])), 2)
        self.assertIn("edge_stack", state)
        self.assertIn("component_trace", state)

    def test_bridges_articulation_finds_biconnected_cycle_component(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D"],
            edges=[("A", "B", 1), ("B", "C", 1), ("C", "A", 1), ("C", "D", 1)],
        )

        steps = list(registry.get("graph/bridges_articulation").run(graph, {}))
        state = steps[-1].state
        components = state.get("biconnected_components", [])

        self.assertIn("C", state.get("articulation_points", []))
        self.assertEqual(len(state.get("bridges", [])), 1)
        self.assertTrue(any(set(component.get("nodes", [])) == {"A", "B", "C"} for component in components))
        self.assertTrue(any(set(component.get("nodes", [])) == {"C", "D"} for component in components))

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

    def test_push_relabel_computes_max_flow(self):
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

        steps = list(registry.get("graph/push_relabel").run(graph, {"source": "S", "target": "T"}))
        state = steps[-1].state

        self.assertEqual(state.get("max_flow"), 23)
        self.assertIn("heights", state)
        self.assertIn("excess", state)
        self.assertIn("push_trace", state)
        self.assertIn("relabel_trace", state)
        self.assertTrue(state.get("push_trace"))
        self.assertTrue(state.get("relabel_trace"))

    def test_hopcroft_karp_computes_maximum_matching(self):
        graph = make_graph(
            directed=False,
            nodes=["L1", "L2", "L3", "R1", "R2", "R3"],
            edges=[
                ("L1", "R1", 1),
                ("L1", "R2", 1),
                ("L2", "R1", 1),
                ("L2", "R3", 1),
                ("L3", "R2", 1),
                ("L3", "R3", 1),
            ],
        )

        steps = list(registry.get("graph/hopcroft_karp").run(graph, {}))

        self.assertEqual(steps[-1].state.get("matching_size"), 3)
        self.assertEqual(len(steps[-1].state.get("matching")), 3)
        self.assertIn("left_partition", steps[-1].state)
        self.assertIn("right_partition", steps[-1].state)

    def test_blossom_matching_handles_odd_cycle(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D", "E"],
            edges=[
                ("A", "B", 1),
                ("B", "C", 1),
                ("C", "A", 1),
                ("A", "D", 1),
                ("B", "E", 1),
            ],
        )

        steps = list(registry.get("graph/blossom_matching").run(graph, {}))
        state = steps[-1].state

        self.assertEqual(state.get("matching_size"), 2)
        self.assertIn("augmenting_paths", state)
        self.assertIn("blossom_trace", state)
        self.assertIn("alternating_forest", state)
        self.assertTrue(state.get("blossom_trace"))

    def test_min_cost_max_flow_computes_flow_and_cost(self):
        graph = Graph(
            directed=True,
            nodes=[{"id": node_id, "label": node_id} for node_id in ["S", "A", "B", "T"]],
            edges=[
                {"id": "S-A", "source": "S", "target": "A", "weight": 2, "directed": True, "metadata": {"capacity": 2, "cost": 1}},
                {"id": "S-B", "source": "S", "target": "B", "weight": 1, "directed": True, "metadata": {"capacity": 1, "cost": 2}},
                {"id": "A-B", "source": "A", "target": "B", "weight": 1, "directed": True, "metadata": {"capacity": 1, "cost": 1}},
                {"id": "A-T", "source": "A", "target": "T", "weight": 1, "directed": True, "metadata": {"capacity": 1, "cost": 3}},
                {"id": "B-T", "source": "B", "target": "T", "weight": 2, "directed": True, "metadata": {"capacity": 2, "cost": 1}},
            ],
        )

        steps = list(registry.get("graph/min_cost_max_flow").run(graph, {"source": "S", "target": "T"}))

        self.assertEqual(steps[-1].state.get("max_flow"), 3)
        self.assertEqual(steps[-1].state.get("min_cost"), 10)
        self.assertIn("flow_table", steps[-1].state)
        self.assertIn("augmentations", steps[-1].state)

    def test_stoer_wagner_finds_global_min_cut(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D", "E", "F"],
            edges=[
                ("A", "B", 4),
                ("A", "C", 3),
                ("B", "D", 3),
                ("C", "D", 4),
                ("C", "E", 1),
                ("D", "F", 1),
                ("E", "F", 5),
            ],
        )

        steps = list(registry.get("graph/stoer_wagner").run(graph, {}))
        state = steps[-1].state

        self.assertEqual(state.get("best_cut_value"), 2)
        self.assertIn(set(state.get("best_cut")), [{"E", "F"}, {"A", "B", "C", "D"}])
        self.assertIn("phase_cuts", state)
        self.assertIn("contractions", state)
        self.assertEqual({edge["edge"] for edge in state.get("min_cut_edges", [])}, {"C-E", "D-F"})

    def test_gomory_hu_tree_answers_all_pairs_min_cuts(self):
        graph = make_graph(
            directed=False,
            nodes=["A", "B", "C", "D", "E", "F"],
            edges=[
                ("A", "B", 4),
                ("A", "C", 3),
                ("B", "D", 3),
                ("C", "D", 4),
                ("C", "E", 1),
                ("D", "F", 1),
                ("E", "F", 5),
            ],
        )

        steps = list(registry.get("graph/gomory_hu_tree").run(graph, {}))
        state = steps[-1].state
        pair_values = {
            (row["source"], row["target"]): row["min_cut"]
            for row in state.get("all_pairs_min_cuts", [])
        }

        self.assertEqual(len(state.get("gomory_hu_tree", [])), 5)
        self.assertEqual(pair_values.get(("A", "E")), 2)
        self.assertEqual(pair_values.get(("E", "F")), 6)
        self.assertIn("cut_iterations", state)
        self.assertEqual(len(state.get("cut_iterations", [])), 5)

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

    def test_sparse_table_answers_static_range_minimum(self):
        steps = list(
            registry.get("array/sparse_table").run(
                Graph(),
                {"values": "7,2,3,0,5,10,3,12,18", "query_left": "1", "query_right": "6", "operation": "min"},
            )
        )

        self.assertEqual(steps[0].action.value, "render_matrix")
        self.assertEqual(steps[-1].state.get("query_result"), 0)
        self.assertEqual(steps[-1].state.get("query_level"), 2)
        self.assertEqual(len(steps[-1].state.get("query_blocks")), 2)
        self.assertIn("sparse_table", steps[-1].state)
        self.assertIn("log_table", steps[-1].state)

    def test_hungarian_finds_minimum_assignment(self):
        steps = list(registry.get("dp/hungarian").run(Graph(), {"costs": "9,2,7;6,4,3;5,8,1"}))

        self.assertEqual(steps[0].action.value, "render_matrix")
        self.assertEqual(steps[-1].state.get("min_cost"), 9)
        self.assertEqual(len(steps[-1].state.get("assignment")), 3)
        self.assertIn("reduced_matrix", steps[-1].state)

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

    def test_segment_tree_computes_range_sum_and_update(self):
        steps = list(
            registry.get("tree/segment_tree").run(
                Graph(),
                {
                    "values": "2,1,5,3,4,7",
                    "query_left": "1",
                    "query_right": "4",
                    "update_index": "3",
                    "update_value": "10",
                },
            )
        )

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("range_sum"), 13)
        self.assertTrue(steps[-1].state.get("update_applied"))
        self.assertEqual(steps[-1].state.get("values"), [2, 1, 5, 10, 4, 7])
        self.assertIn("accepted_nodes", steps[-1].state)

    def test_lca_finds_lowest_common_ancestor(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C", "D", "E", "F", "G"],
            edges=[
                ("A", "B", 1),
                ("A", "C", 1),
                ("B", "D", 1),
                ("B", "E", 1),
                ("C", "F", 1),
                ("C", "G", 1),
            ],
        )
        graph.root_id = "A"

        steps = list(registry.get("tree/lca").run(graph, {"source": "A", "node_a": "D", "node_b": "E"}))
        state = steps[-1].state

        self.assertEqual(state.get("lca"), "B")
        self.assertEqual(state.get("depth", {}).get("D"), 2)
        self.assertEqual(state.get("depth", {}).get("E"), 2)
        self.assertIn("ancestor_table", state)
        self.assertIn("lift_trace", state)
        self.assertEqual(state.get("lca_path"), ["D", "B", "E"])

    def test_heavy_light_decomposition_splits_path_into_chain_segments(self):
        graph = make_graph(
            directed=True,
            nodes=["A", "B", "C", "D", "E", "F", "G"],
            edges=[
                ("A", "B", 1),
                ("A", "C", 1),
                ("B", "D", 1),
                ("B", "E", 1),
                ("C", "F", 1),
                ("C", "G", 1),
            ],
        )
        graph.root_id = "A"

        steps = list(
            registry.get("tree/heavy_light_decomposition").run(
                graph,
                {"source": "A", "node_a": "D", "node_b": "G", "values": "1,2,3,4,5,6,7"},
            )
        )
        state = steps[-1].state

        self.assertEqual(state.get("path_query_result"), 17)
        self.assertEqual(state.get("path_nodes"), ["D", "B", "A", "C", "G"])
        self.assertIn("heavy_child", state)
        self.assertIn("head", state)
        self.assertIn("position", state)
        self.assertIn("base_array", state)
        self.assertTrue(state.get("path_segments"))

    def test_trie_tracks_prefix_counts_and_deletion(self):
        steps = list(
            registry.get("tree/trie").run(
                Graph(),
                {"words": "app,apple,apt,bat", "query_prefix": "ap", "delete_words": "app"},
            )
        )
        state = steps[-1].state

        self.assertEqual(state.get("prefix_query_result", {}).get("count"), 2)
        self.assertTrue(state.get("prefix_query_result", {}).get("after_deletion"))
        self.assertEqual(state.get("word_frequency"), {"apple": 1, "apt": 1, "bat": 1})
        self.assertEqual(state.get("deleted_words"), ["app"])
        self.assertTrue(state.get("deletion_results", [{}])[0].get("deleted"))
        self.assertIn("trie_nodes", state)
        self.assertIn("remaining_word_count", state)

    def test_aho_corasick_reports_failure_links_and_outputs(self):
        steps = list(
            registry.get("tree/aho_corasick").run(
                Graph(),
                {"patterns": "he,she,his,hers", "text": "ushers"},
            )
        )
        state = steps[-1].state
        matches = {(match["pattern"], match["start"], match["end"]) for match in state.get("matches", [])}

        self.assertEqual(state.get("match_count"), 3)
        self.assertIn(("she", 1, 3), matches)
        self.assertIn(("he", 2, 3), matches)
        self.assertIn(("hers", 2, 5), matches)
        self.assertIn("failure_links", state)
        self.assertIn("output_table", state)
        self.assertIn("failure_trace", state)
        self.assertEqual(len(state.get("scan_trace", [])), 6)

    def test_avl_deletes_values_and_reports_rebalancing(self):
        steps = list(
            registry.get("tree/avl").run(
                Graph(),
                {"values": "20,10,30,5,15,25,40,2,7", "delete_values": "30,10"},
            )
        )

        self.assertEqual(steps[-1].state.get("deleted_values"), [30, 10])
        self.assertNotIn(30, steps[-1].state.get("inorder"))
        self.assertNotIn(10, steps[-1].state.get("inorder"))
        deletion_step = next(step for step in steps if step.state and step.state.get("deleted_value") == 30)
        self.assertIn("delete_path", deletion_step.state)
        self.assertIn("rebalancing", deletion_step.state)

    def test_red_black_deletes_values_and_reports_fixup(self):
        steps = list(
            registry.get("tree/red_black").run(
                Graph(),
                {"values": "20,10,30,5,15,25,40,1,7", "delete_values": "5,30"},
            )
        )

        self.assertEqual(steps[-1].state.get("deleted_values"), [5, 30])
        values = [item["value"] for item in steps[-1].state.get("inorder")]
        self.assertNotIn(5, values)
        self.assertNotIn(30, values)
        self.assertEqual(steps[-1].state.get("root_color"), "black")
        deletion_step = next(step for step in steps if step.state and step.state.get("deleted_value") == 5)
        self.assertIn("delete_path", deletion_step.state)
        self.assertIn("fixup_cases", deletion_step.state)

    def test_treap_preserves_bst_order_and_heap_priorities(self):
        steps = list(
            registry.get("tree/treap").run(
                Graph(),
                {"values": "50,30,70,20,40,60,80", "priorities": "50,30,40,10,35,20,60"},
            )
        )

        self.assertEqual(steps[-1].state.get("inorder"), [20, 30, 40, 50, 60, 70, 80])
        self.assertTrue(steps[-1].state.get("heap_valid"))
        self.assertGreater(len(steps[-1].state.get("rotations")), 0)
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

    def test_suffix_array_finds_pattern_matches(self):
        steps = list(registry.get("string/suffix_array").run(Graph(), {"text": "banana", "pattern": "ana"}))

        self.assertEqual(steps[0].action.value, "render_array")
        self.assertEqual(steps[-1].state.get("suffix_array"), [5, 3, 1, 0, 4, 2])
        self.assertEqual(steps[-1].state.get("matches"), [1, 3])

    def test_suffix_automaton_builds_substring_index(self):
        steps = list(registry.get("string/suffix_automaton").run(Graph(), {"text": "abcbc", "query": "bcb"}))
        state = steps[-1].state

        self.assertEqual(state.get("distinct_substring_count"), 12)
        self.assertEqual(state.get("longest_repeated_substring"), "bc")
        self.assertTrue(state.get("query_found"))
        self.assertIn("suffix_links", state)
        self.assertIn("transition_table", state)
        self.assertIn("clone_trace", state)
        self.assertTrue(state.get("clone_trace"))


if __name__ == "__main__":
    unittest.main()

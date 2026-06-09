import unittest

from knot.graph import find_cycles, strongly_connected_components


class StronglyConnectedComponentsTests(unittest.TestCase):
    def test_acyclic_graph_has_singleton_components(self):
        edges = {"a": {"b"}, "b": {"c"}, "c": set()}
        comps = strongly_connected_components(edges)
        self.assertEqual(sorted(sorted(c) for c in comps), [["a"], ["b"], ["c"]])

    def test_detects_multi_node_scc(self):
        edges = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
        comps = [sorted(c) for c in strongly_connected_components(edges)]
        self.assertIn(["a", "b", "c"], comps)

    def test_handles_large_chain_without_recursion_error(self):
        # Iterative Tarjan must survive deep graphs.
        n = 5000
        edges = {str(i): {str(i + 1)} for i in range(n)}
        edges[str(n)] = set()
        comps = strongly_connected_components(edges)
        self.assertEqual(len(comps), n + 1)


class FindCyclesTests(unittest.TestCase):
    def test_no_cycle(self):
        edges = {"a": {"b"}, "b": set()}
        self.assertEqual(find_cycles(edges), [])

    def test_two_node_cycle(self):
        edges = {"a": {"b"}, "b": {"a"}}
        cycles = find_cycles(edges)
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0].members, ["a", "b"])
        # example path is a closed loop
        self.assertEqual(cycles[0].example_path[0], cycles[0].example_path[-1])

    def test_self_import_is_a_cycle(self):
        edges = {"a": {"a"}}
        cycles = find_cycles(edges)
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0].members, ["a"])
        self.assertEqual(cycles[0].example_path, ["a", "a"])

    def test_cycles_sorted_largest_first(self):
        edges = {
            # 3-cycle
            "a": {"b"}, "b": {"c"}, "c": {"a"},
            # 2-cycle
            "x": {"y"}, "y": {"x"},
        }
        cycles = find_cycles(edges)
        self.assertEqual([c.size for c in cycles], [3, 2])


if __name__ == "__main__":
    unittest.main()

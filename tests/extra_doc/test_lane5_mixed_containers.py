"""Cross-cutting mixed-row acceptance/refusal checks for delivered lane5 APIs."""
import unittest
from sugarcode.extra_doc.neuromorphic921 import simulate_array
from sugarcode.extra_doc.quantum_network920 import best_entanglement_route
from sugarcode.extra_doc.spiking922 import event_neuron


class MixedContainerTests(unittest.TestCase):
    def test_921_mixed_matrix_rows_in_both_orders(self):
        for current_rows in ([[1, 0], (0, 1)], [(1, 0), [0, 1]]):
            for weight_rows in ([[0, 0], (0, 0)], [(0, 0), [0, 0]]):
                self.assertEqual(simulate_array(current_rows, weight_rows),
                                 simulate_array([[1, 0], [0, 1]], [[0, 0], [0, 0]]))

    def test_920_mixed_edge_rows_have_declared_refusal(self):
        for rows in ([('a', 'b', 1, 1), ['b', 'c', 1, 1]],
                     [['b', 'c', 1, 1], ('a', 'b', 1, 1)]):
            with self.assertRaises(ValueError) as caught:
                best_entanglement_route(rows, 'a', 'c')
            self.assertEqual(str(caught.exception), 'each edge must be an exact four-item tuple')

    def test_922_mixed_event_rows_have_declared_refusal(self):
        for rows in ([(0, 1), [1, 1]], [[1, 1], (0, 1)]):
            with self.assertRaises(ValueError) as caught:
                event_neuron(rows)
            self.assertEqual(str(caught.exception), 'each event must be an exact pair tuple')

    def test_920_declared_label_charset(self):
        for label in ('a-b', 'é', 'a b', 'a_'):
            with self.assertRaises(ValueError) as caught:
                best_entanglement_route([(label, 'B', 1, 1)], label, 'B')
            self.assertEqual(str(caught.exception),
                             'node labels must be 1..24 ASCII alphanumeric strings')
        self.assertEqual(best_entanglement_route([('A1', 'B2', 1, 1)], 'A1', 'B2')['path'],
                         ('A1', 'B2'))


if __name__ == '__main__':
    unittest.main()

import importlib
import importlib.util
import itertools
import math
import os
import sys
import unittest


def load(name):
    full = 'sugarcode.extra_doc.' + name
    if os.environ.get('MUTANT_MODULE') == full:
        spec = importlib.util.spec_from_file_location(full, os.environ['MUTANT_PATH'])
        module = importlib.util.module_from_spec(spec)
        sys.modules[full] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(full)


a = load('quantum_application913')
b = load('quantum_design914')


class IntSubclass(int):
    pass


class QuantumTests(unittest.TestCase):
    def test_grover_oracle_and_norm(self):
        for n in range(1, 6):
            size = 2 ** n
            for count in range(size + 1):
                for iterations in (0, 1, 2, 5):
                    out = a.grover_search(n, list(range(count)), iterations)
                    theta = math.asin(math.sqrt(count / size))
                    self.assertAlmostEqual(out['success_probability'], math.sin((2 * iterations + 1) * theta) ** 2, places=11)
                    self.assertAlmostEqual(out['norm'], 1, places=11)
                    self.assertEqual(out['oracle_queries'], iterations)
                    self.assertAlmostEqual(out['predicted_probability'], out['success_probability'], places=11)
        self.assertEqual(a.grover_search(2, [3])['oracle_queries'], 1)
        self.assertAlmostEqual(a.grover_search(2, [3])['state'][3], 1)
        self.assertEqual(a.grover_search(3, [])['oracle_queries'], 0)
        self.assertEqual(a.grover_search(3, list(range(8)))['oracle_queries'], 0)
        self.assertEqual(a.grover_search(12, [], 0)['marked_count'], 0)
        self.assertEqual(a.grover_search(1, [], 10000)['oracle_queries'], 10000)

    def test_grover_rejections(self):
        for n in (True, IntSubclass(2), 0, 13, 2.0, '2'):
            with self.assertRaises(ValueError): a.grover_search(n, [])
        for marked in ([True], [IntSubclass(1)], [-1], [4], [1, 1], {1}, '1', None):
            with self.assertRaises(ValueError): a.grover_search(2, marked)
        for iterations in (True, IntSubclass(1), -1, 10001, 1.0):
            with self.assertRaises(ValueError): a.grover_search(2, [], iterations)

    def test_bv_exhaustive_and_gate_structure(self):
        for n in range(1, 6):
            for bits in itertools.product('01', repeat=n):
                secret = ''.join(bits)
                out = b.bernstein_vazirani(secret)
                self.assertEqual(out['decoded'], secret)
                self.assertAlmostEqual(out['probabilities'][int(secret, 2)], 1, places=11)
                self.assertAlmostEqual(sum(out['probabilities']), 1, places=11)
                self.assertEqual(out['gates'][0], ('X', n))
                self.assertEqual(out['cnot_count'], secret.count('1'))
                self.assertEqual(out['oracle_calls'], 1)
                self.assertEqual(sum(g[0] == 'H' for g in out['gates']), 2*n+1)
                controls = [g[1] for g in out['gates'] if g[0] == 'CX']
                self.assertEqual(controls, [q for q, x in enumerate(secret[::-1]) if x == '1'])
        self.assertEqual(b.bernstein_vazirani('10000000001')['decoded'], '10000000001')

    def test_bv_rejections(self):
        class StringSubclass(str): pass
        for secret in ('', '2', '01x', '1'*12, 1, None, StringSubclass('1')):
            with self.assertRaises(ValueError): b.bernstein_vazirani(secret)


if __name__ == '__main__': unittest.main()

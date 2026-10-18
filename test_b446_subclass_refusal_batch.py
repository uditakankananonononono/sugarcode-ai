import importlib
import inspect
import signal
import unittest
from fractions import Fraction


class PlainInt(int):
    pass


class LieInt(int):
    """int subclass whose comparisons deny being out of range."""
    def __gt__(self, o): return False
    def __lt__(self, o): return False
    def __ge__(self, o): return False
    def __le__(self, o): return False


class PlainList(list):
    pass


class PlainTuple(tuple):
    pass


class PlainStr(str):
    pass


class PlainFraction(Fraction):
    pass


G2 = [[0, 1], [1, 0]]
BASES = {
    'b446_intervals': dict(a=(1, 2), b=(3, 4), exponent=2),
    'b446_games': dict(n=2, values=[0, 1, 2, 4], dividends=[0, 1, 1, 1],
                       mask=1, player=1, allocation=[1, 2]),
    'b446_groups': dict(table=G2, generators=[1]),
    'b446_divisors': dict(n=12, k=3, values=[1, 2, 3], left=[1, 2, 3],
                          right=[1, 1, 1]),
    'b446_permutation': dict(p=[2, 0, 1], n=4, k=1, step=2),
    'b446_knapsack': dict(weights=[1, 2, 3], target=4, counts=[1, 1, 1],
                          values=[1, 2, 3], cardinality=2),
    'b446_graphs': dict(n=3, edges=[(0, 1), (1, 2)], colors=3),
    'b446_next': dict(a='ab', b='ba'),
}


def variants(obj):
    """Yield (label, copy of obj with exactly one node swapped for a subclass)."""
    t = type(obj)
    if t is int:
        yield 'PlainInt', PlainInt(obj)
        yield 'LieInt', LieInt(obj)
    elif t is str:
        yield 'PlainStr', PlainStr(obj)
    elif t is Fraction:
        yield 'PlainFraction', PlainFraction(obj)
    elif t in (list, tuple):
        yield 'container', (PlainList if t is list else PlainTuple)(obj)
        for i, x in enumerate(obj):
            for label, v in variants(x):
                new = list(obj)
                new[i] = v
                yield label, t(new)


def _timeout(*a):
    raise TimeoutError('hang')


class SubclassRefusal(unittest.TestCase):
    def setUp(self):
        signal.signal(signal.SIGALRM, _timeout)

    def tearDown(self):
        signal.alarm(0)

    def check_module(self, name):
        mod = importlib.import_module(name)
        base = BASES[name]
        count = 0
        for fname, f in inspect.getmembers(mod, inspect.isfunction):
            if fname.startswith('_') or f.__module__ != name:
                continue
            params = list(inspect.signature(f).parameters)
            args = [base[p] for p in params]
            signal.alarm(10)
            f(*args)  # the plain call must be accepted, list and tuple alike
            for i in range(len(args)):
                for label, v in variants(args[i]):
                    a = list(args)
                    a[i] = v
                    with self.subTest(fn=fname, param=params[i], kind=label):
                        with self.assertRaises(TypeError):
                            f(*a)
                    count += 1
            signal.alarm(0)
        self.assertGreater(count, 10)

    def test_intervals(self): self.check_module('b446_intervals')
    def test_games(self): self.check_module('b446_games')
    def test_groups(self): self.check_module('b446_groups')
    def test_divisors(self): self.check_module('b446_divisors')
    def test_permutation(self): self.check_module('b446_permutation')
    def test_knapsack(self): self.check_module('b446_knapsack')
    def test_graphs(self): self.check_module('b446_graphs')
    def test_next(self): self.check_module('b446_next')

    def test_lie_int_cannot_bypass_caps(self):
        import b446_games as g, b446_intervals as iv, b446_groups as gr
        import b446_divisors as dv, b446_knapsack as kn, b446_permutation as pm
        signal.alarm(10)
        for f, a in [
            (g.shapley_values, (LieInt(10 ** 30), [0])),
            (g.coalition_value, (1, [0, 1], LieInt(10 ** 30))),
            (iv.interval_power, ((1, 2), LieInt(10 ** 30))),
            (iv.interval_power, ((0, 1), LieInt(-5))),
            (gr.subgroup_generated, (G2, [1, LieInt(10 ** 7)])),
            (dv.divisor_count, (LieInt(10 ** 9),)),
            (kn.subset_sum_count, ([1, 2], LieInt(10 ** 9))),
            (pm.josephus_survivor, (LieInt(10 ** 9), 2)),
        ]:
            with self.subTest(fn=f.__name__):
                with self.assertRaises(TypeError):
                    f(*a)


if __name__ == '__main__':
    unittest.main()

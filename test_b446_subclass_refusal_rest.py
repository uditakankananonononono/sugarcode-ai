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


class PlainDict(dict):
    pass


class IterHostileList(list):
    def __iter__(self):
        raise RuntimeError('hostile __iter__')


class IterHostileTuple(tuple):
    def __iter__(self):
        raise RuntimeError('hostile __iter__')


class IndexHostileInt(int):
    def __index__(self):
        raise RuntimeError('hostile __index__')
    __gt__ = __lt__ = __ge__ = __le__ = lambda self, o: False


class PlainFraction(Fraction):
    pass


BASES = {
    'b446_new': dict(law={1: 2, 3: 5}, left={1: 2, 3: 5}, right={0: 1, 2: 1}, threshold=2, values=[1, 3],
                     numerator=1, denominator=2, order=2),
    'b446_sets': dict(left=[1, 2, 3], right=[2, 3, 4], groups=[[1, 2], [2, 3], [3, 4]], degree=2),
    'b446_matrices': dict(matrix=[[2, 1], [1, 3]], rhs=[1, 2]),
    'b446_latin': dict(table=[[0, 1], [1, 0]], left=[[0, 1], [1, 0]], right=[[0, 1], [1, 0]]),
    'b446_quaternion': dict(a=(1, 2, 3, 4), b=(0, 1, 0, 2), exponent=2, vector=(1, 0, 0)),
    'b446_topology': dict(n=3, opens=[0, 1, 3, 7], mask=3),
    'b446_metric': dict(matrix=[[0, 1, 2], [1, 0, 1], [2, 1, 0]], ball_radius=1, separation=1),
    'row392_new': dict(p=7, q=3, r=5, s=2, limit=10, terms=[2, 3, 4]),
}


def variants(obj):
    """Yield (label, copy of obj with exactly one node swapped for a subclass)."""
    t = type(obj)
    if t is int:
        yield 'PlainInt', PlainInt(obj)
        yield 'LieInt', LieInt(obj)
        yield 'IndexHostileInt', IndexHostileInt(obj)
    elif t is str:
        yield 'PlainStr', PlainStr(obj)
    elif t is Fraction:
        yield 'PlainFraction', PlainFraction(obj)
    elif t is dict:
        yield 'container', PlainDict(obj)
        for k, x in obj.items():
            for label, v in variants(x):
                new = dict(obj)
                new[k] = v
                yield label + '-value', new
            for label, v in variants(k):
                new = {(v if kk == k else kk): vv for kk, vv in obj.items()}
                yield label + '-key', new
    elif t in (list, tuple):
        yield 'container', (PlainList if t is list else PlainTuple)(obj)
        yield 'iter-hostile', (IterHostileList if t is list else IterHostileTuple)(obj)
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

    def test_new(self): self.check_module('b446_new')
    def test_sets(self): self.check_module('b446_sets')
    def test_matrices(self): self.check_module('b446_matrices')
    def test_latin(self): self.check_module('b446_latin')
    def test_quaternion(self): self.check_module('b446_quaternion')
    def test_topology(self): self.check_module('b446_topology')
    def test_metric(self): self.check_module('b446_metric')
    def test_row392(self): self.check_module('row392_new')

    def test_lie_int_cannot_bypass_caps(self):
        import b446_matrices as mx, b446_metric as me, row392_new as rw, b446_topology as tp, b446_quaternion as qu
        signal.alarm(10)
        for f, a in [
            (mx.determinant, ([[LieInt(10 ** 30)]],)),
            (me.covering_number, ([[0, 1], [1, 0]], LieInt(10 ** 30))),
            (rw.rational_floor, (LieInt(10 ** 30), 1)),
            (tp.closure, (LieInt(10 ** 9), [0], 0)),
            (qu.integer_power, ((1, 0, 0, 0), LieInt(10 ** 9))),
        ]:
            with self.subTest(fn=f.__name__):
                with self.assertRaises(TypeError):
                    f(*a)


if __name__ == '__main__':
    unittest.main()

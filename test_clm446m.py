"""clm446m pins: the confirmed b446_matrices cap bypass witnesses.

Confirmed bypass (pre-repair image): an int subclass whose __abs__ returns 0
passed the MAX_ENTRY cap (isinstance accepted it, abs() lied), and list/tuple
subclasses were accepted as matrix, row and rhs containers. The repair image
refuses every non-exact type at the entry, matrix, row and rhs sites with the
site's coded TypeError. Every pin here FAILS on the pre-repair image: the
witness is accepted and computes instead of raising.
"""
import unittest
import b446_matrices as m


class AbsZeroInt(int):
    """int subclass whose abs() reports 0, defeating abs(x) > MAX_ENTRY."""

    def __abs__(self):
        return 0


class PlainList(list):
    pass


class PlainTuple(tuple):
    pass


class IterHostileList(list):
    def __iter__(self):
        raise RuntimeError('hostile __iter__')


class IterHostileTuple(tuple):
    def __iter__(self):
        raise RuntimeError('hostile __iter__')


MATRIX_FUNCS = [m.determinant, m.permanent, m.rank, m.nullity, m.inverse,
                m.adjugate, m.trace, m.gram_matrix, m.rref]
GOOD = ((2, 1), (1, 3))


class AbsBypassRefused(unittest.TestCase):
    def test_abs_zero_int_refused_at_matrix_entries(self):
        for f in MATRIX_FUNCS:
            for pos in ((0, 0), (1, 1)):
                mat = [list(row) for row in GOOD]
                mat[pos[0]][pos[1]] = AbsZeroInt(10 ** 30)
                with self.subTest(fn=f.__name__, pos=pos):
                    with self.assertRaisesRegex(TypeError, '^entry must be an integer$'):
                        f(mat)
        for pos in ((0, 0), (1, 1)):
            mat = [list(row) for row in GOOD]
            mat[pos[0]][pos[1]] = AbsZeroInt(10 ** 30)
            with self.subTest(fn='solve', pos=pos):
                with self.assertRaisesRegex(TypeError, '^entry must be an integer$'):
                    m.solve(mat, [1, 2])

    def test_abs_zero_int_refused_at_rhs_entries(self):
        for pos in (0, 1):
            rhs = [1, 2]
            rhs[pos] = AbsZeroInt(10 ** 30)
            with self.subTest(pos=pos):
                with self.assertRaisesRegex(TypeError, '^entry must be an integer$'):
                    m.solve(GOOD, rhs)

    def test_abs_zero_int_would_have_been_a_real_bypass(self):
        # The witness is a genuine int subclass: arithmetic on it works,
        # so on the pre-repair image the calls above returned huge results.
        self.assertIsInstance(AbsZeroInt(10 ** 30), int)
        self.assertEqual(abs(AbsZeroInt(10 ** 30)), 0)
        self.assertGreater(int(AbsZeroInt(10 ** 30)), m.MAX_ENTRY)


class ContainerSubclassRefused(unittest.TestCase):
    def test_matrix_subclasses_refused(self):
        for f in MATRIX_FUNCS:
            for bad in (PlainList(GOOD), PlainTuple(GOOD),
                        IterHostileList(GOOD), IterHostileTuple(GOOD)):
                with self.subTest(fn=f.__name__, bad=type(bad).__name__):
                    with self.assertRaisesRegex(TypeError, '^matrix must be a list or tuple$'):
                        f(bad)
        for bad in (PlainList(GOOD), PlainTuple(GOOD),
                    IterHostileList(GOOD), IterHostileTuple(GOOD)):
            with self.subTest(fn='solve', bad=type(bad).__name__):
                with self.assertRaisesRegex(TypeError, '^matrix must be a list or tuple$'):
                    m.solve(bad, [1, 2])

    def test_row_subclasses_refused(self):
        for bad_row in (PlainList((2, 1)), PlainTuple((2, 1)),
                        IterHostileList((2, 1)), IterHostileTuple((2, 1))):
            with self.subTest(bad=type(bad_row).__name__):
                with self.assertRaisesRegex(TypeError, '^row must be a list or tuple$'):
                    m.trace([bad_row, (1, 3)])

    def test_rhs_subclasses_refused(self):
        for bad in (PlainList([1, 2]), PlainTuple((1, 2)),
                    IterHostileList([1, 2]), IterHostileTuple([1, 2])):
            with self.subTest(bad=type(bad).__name__):
                with self.assertRaisesRegex(TypeError, '^rhs must be a list or tuple$'):
                    m.solve(GOOD, bad)

    def test_plain_containers_still_accepted(self):
        # No over-broad refusal: exact list/tuple inputs compute as before.
        self.assertEqual(m.determinant([[2, 1], [1, 3]]), 5)
        self.assertEqual(m.determinant(((2, 1), (1, 3))), 5)
        self.assertEqual(m.trace([[2, 1], [1, 3]]), 5)
        self.assertEqual(m.solve(((2, 1), (1, 3)), (1, 2)), (m.Fraction(1, 5), m.Fraction(3, 5)))


if __name__ == '__main__':
    unittest.main()

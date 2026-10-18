"""clm446met pins: the confirmed b446_metric subclass witnesses.

Sugarcode lane 8 witnesses, all reproduced raw on the pre-repair image:
lying-__len__ row subclass -> raw IndexError in all 10 public functions;
empty tuple subclass with lying __len__ -> false is_metric certificate (True),
raw ValueError from max() in diameter, raw AssertionError in covering_number /
packing_number; list subclass matrix and int subclass entries accepted.
The repair image (b446-subclass-refusal-rest) refuses every non-exact type at
the matrix, row, entry and radius sites with the site's coded TypeError.
Every refusal pin here FAILS on the pre-repair image.
"""
import unittest
import b446_metric as m

M3 = ((0, 1, 2), (1, 0, 1), (2, 1, 0))


class R(tuple):
    """Row subclass whose __len__ lies (reports 1 for an empty row)."""

    def __len__(self):
        return 1


class E1(tuple):
    """Empty tuple subclass whose __len__ lies (reports 1)."""

    def __len__(self):
        return 1


class LL(list):
    pass


class TT(tuple):
    pass


class I(int):
    pass


class LieInt(int):
    def __lt__(s, o): return False
    def __gt__(s, o): return False
    def __le__(s, o): return False
    def __ge__(s, o): return False


MATRIX_ONLY = [m.metric_defect_count, m.is_metric, m.diameter, m.eccentricities,
               m.radius, m.centers, m.is_ultrametric, m.four_point_hyperbolicity]
ALL10 = MATRIX_ONLY + [m.covering_number, m.packing_number]


def call(f, matrix):
    if f in (m.covering_number, m.packing_number):
        return f(matrix, 0)
    return f(matrix)


class LyingLenRowRefused(unittest.TestCase):
    def test_all_ten(self):
        for f in ALL10:
            with self.subTest(fn=f.__name__):
                with self.assertRaisesRegex(TypeError, '^row must be a list or tuple$'):
                    call(f, (R(()),))

    def test_witness_is_genuine(self):
        r = R(())
        self.assertIsInstance(r, tuple)
        self.assertEqual(len(r), 1)


class EmptySubclassMatrixRefused(unittest.TestCase):
    def test_all_ten(self):
        for f in ALL10:
            with self.subTest(fn=f.__name__):
                with self.assertRaisesRegex(TypeError, '^matrix must be a list or tuple$'):
                    call(f, E1())

    def test_witness_is_genuine(self):
        e = E1()
        self.assertIsInstance(e, tuple)
        self.assertEqual(len(e), 1)


class ContainerAndEntrySubclassesRefused(unittest.TestCase):
    def test_list_and_tuple_subclass_matrices(self):
        for f in ALL10:
            for bad in (LL([[0, 1], [1, 0]]), TT(((0, 1), (1, 0)))):
                with self.subTest(fn=f.__name__, bad=type(bad).__name__):
                    with self.assertRaisesRegex(TypeError, '^matrix must be a list or tuple$'):
                        call(f, bad)

    def test_row_subclasses(self):
        for bad_row in (LL([0, 1]), TT((0, 1)), R((0, 1))):
            with self.subTest(bad=type(bad_row).__name__):
                with self.assertRaisesRegex(TypeError, '^row must be a list or tuple$'):
                    m.diameter([bad_row, (1, 0)])

    def test_entry_subclasses(self):
        for bad in (I(0), LieInt(5), True, 1.5, 'a', None):
            with self.subTest(bad=repr(bad)):
                with self.assertRaisesRegex(TypeError, '^distance must be an integer$'):
                    m.diameter(([bad],))
            with self.subTest(bad=repr(bad), fn='covering'):
                with self.assertRaisesRegex(TypeError, '^distance must be an integer$'):
                    m.covering_number([[0, bad], [1, 0]], 1)

    def test_radius_subclasses(self):
        for bad in (I(1), LieInt(1), True, 1.5, 'a', None):
            for f in (m.covering_number, m.packing_number):
                with self.subTest(fn=f.__name__, bad=repr(bad)):
                    with self.assertRaisesRegex(TypeError, '^radius must be an integer$'):
                        f([[0]], bad)


class AcceptancePreserved(unittest.TestCase):
    def test_golden_valid_metric(self):
        self.assertEqual(m.diameter(M3), 2)
        self.assertEqual(m.eccentricities(M3), (2, 1, 2))
        self.assertEqual(m.radius(M3), 1)
        self.assertEqual(m.centers(M3), (1,))
        self.assertTrue(m.is_metric(M3))
        self.assertFalse(m.is_ultrametric(M3))
        self.assertEqual(m.covering_number(M3, 1), 1)
        self.assertEqual(m.packing_number(M3, 1), 2)
        self.assertEqual(m.covering_number(M3, 0), 3)
        self.assertEqual(m.metric_defect_count(M3), 0)
        self.assertEqual(m.diameter([[0]]), 0)

    def test_defective_still_coded(self):
        with self.assertRaisesRegex(ValueError, '^matrix must be a metric$'):
            m.diameter(((0, 3), (1, 0)))  # asymmetric
        self.assertEqual(m.metric_defect_count(((0, 3), (1, 0))), 1)
        self.assertFalse(m.is_metric(((0, 3), (1, 0))))


if __name__ == '__main__':
    unittest.main()

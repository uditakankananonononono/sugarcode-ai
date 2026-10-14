from fractions import Fraction as Fr
import random
import pytest
from sugarcode.extra_doc import medical_illustration as m

L = m.layout_labels


def test_constants():
    assert m.MAX_LABELS == 200 and m.STATUS_NOTE.startswith("PARTIAL")
    assert "no anatomical" in m.STATUS_NOTE


def test_hand_layouts():
    r = L([(10, 5), (20, 6), (30, 7)], 100, 200, 10)
    assert r["slots"] == [5, 15, 25] and r["displacement"] == [0, 9, 18] and r["crossings"] == 0
    assert r["status"] == m.STATUS_NOTE
    r = L([(0, 98), (0, 99), (0, 100)], 100, 50, 10)  # pushed up from the bottom edge
    assert r["slots"] == [80, 90, 100] and r["displacement"] == [18, 9, 0]
    assert L([(0, 50), (0, 10)], 100, 50, 5)["slots"] == [50, 10]
    assert L([(5, 10), (3, 10)], 100, 50, 4)["slots"] == [14, 10]   # ties on y go by x then index
    assert L([(1, 10), (1, 10)], 100, 50, 4)["slots"] == [10, 14]
    assert L([(0, 7), (0, 7)], 100, 50, 0)["slots"] == [7, 7]
    assert L([(3, 0), (3, 0), (3, 0)], 100, 50, 50)["slots"] == [0, 50, 100]
    assert L([(3, 100)], 100, 50, 999)["slots"] == [100]
    assert L([(0, 100), (0, 100)], 100, 50, 100)["slots"] == [0, 100]


def test_crossing_hand_case():
    # sorted: (15,2)->2, (32,3)->7, (50,3)->12. Leaders (32,3)-(100,7) and (50,3)-(100,12) cross once.
    r = L([(50, 3), (32, 3), (15, 2)], 20, 100, 5)
    assert r["slots"] == [12, 7, 2] and r["crossings"] == 1


def test_parallel_leaders_do_not_cross_or_touch_count():
    # two leaders ending at the same slot touch at the end point only: not a proper crossing
    assert L([(0, 5), (50, 5)], 100, 100, 0)["crossings"] == 0
    assert L([(0, 0), (0, 10)], 100, 100, 0)["crossings"] == 0


def test_does_not_fit():
    assert L([(0, 0)] * 3, 100, 10, 50)["slots"] == [0, 50, 100]
    with pytest.raises(ValueError, match="labels do not fit at this gap"):
        L([(0, 0)] * 3, 100, 10, 50.5)


def test_slots_are_feasible_random_and_crossings_oracle():
    rnd = random.Random(17)

    def segs_cross(p, q, r, s):  # exact parametric proper-intersection test, independent of the module's orientation helper
        d = (q[0] - p[0]) * (s[1] - r[1]) - (q[1] - p[1]) * (s[0] - r[0])
        if d == 0:
            return False
        t = Fr((r[0] - p[0]) * (s[1] - r[1]) - (r[1] - p[1]) * (s[0] - r[0]), d)
        u = Fr((r[0] - p[0]) * (q[1] - p[1]) - (r[1] - p[1]) * (q[0] - p[0]), d)
        return 0 < t < 1 and 0 < u < 1

    for _ in range(150):
        n = rnd.randint(1, 8)
        h, g, lx = 100, rnd.randint(0, 12), 120
        a = [(rnd.randint(0, 100), rnd.randint(0, 100)) for _ in range(n)]
        r = L(a, h, lx, g)
        s = r["slots"]
        order = sorted(range(n), key=lambda i: (a[i][1], a[i][0], i))
        for x, y in zip(order, order[1:]):
            assert s[y] - s[x] >= g
        assert all(0 <= v <= h for v in s)
        assert r["displacement"] == [abs(s[i] - a[i][1]) for i in range(n)]
        want = sum(segs_cross(a[i], (lx, s[i]), a[j], (lx, s[j])) for i in range(n) for j in range(i + 1, n))
        assert r["crossings"] == want


@pytest.mark.parametrize("args", [
    ([], 100, 50, 1), ([(0, 0)] * 201, 100, 50, 0), ("ab", 100, 50, 1), (None, 100, 50, 1), ([5], 100, 50, 1),
    ([(1,)], 100, 50, 1), ([(1, 2, 3)], 100, 50, 1), ([(True, 1)], 100, 50, 1), ([(1, "2")], 100, 50, 1),
    ([(-1, 1)], 100, 50, 1), ([(100001, 1)], 100, 50, 1), ([(1, -1)], 100, 50, 1), ([(1, 101)], 100, 50, 1),
    ([(1, 1)], 0.5, 50, 1), ([(1, 1)], 100001, 50, 1), ([(1, 1)], True, 50, 1), ([(1, 1)], 100, -1, 1),
    ([(1, 1)], 100, 100001, 1), ([(1, 1)], 100, 50, -1), ([(1, 1)], 100, 50, 1001), ([(1, 1)], 100, 50, True),
    ([(1, float("nan"))], 100, 50, 1), ([(1, 1)], float("inf"), 50, 1), ([(1, 1)], 100, 50, "1"),
    ([(1, 1)], 2e9, 50, 1),
])
def test_rejects(args):
    with pytest.raises(ValueError):
        L(*args)


def test_edges_accepted_and_messages():
    assert len(L([(0, 0)] * 200, 100000, 0, 0)["slots"]) == 200
    assert L([(100000, 100000)], 100000, 100000, 1000)["slots"] == [100000]
    assert L([(0, 1)], 1, 0, 0)["slots"] == [1]
    for kw, msg in [(dict(anchors=[], height=1, label_x=0, gap=0), "anchors: 1 to 200 required"),
                    (dict(anchors=[(1,)], height=1, label_x=0, gap=0), r"anchor: \(x, y\) required"),
                    (dict(anchors=[(0, 0)], height=0.9, label_x=0, gap=0), "height: must be within"),
                    (dict(anchors=[(0, 0)], height=1, label_x=-1, gap=0), "label_x: must be within"),
                    (dict(anchors=[(0, 0)], height=1, label_x=0, gap=1001), "gap: must be within"),
                    (dict(anchors=[(0, 2)], height=1, label_x=0, gap=0), "y: must be within"),
                    (dict(anchors=[(100001, 0)], height=1, label_x=0, gap=0), "x: must be within"),
                    (dict(anchors=[(0, 0)], height=True, label_x=0, gap=0), "height: number required"),
                    (dict(anchors=[(0, 0)], height=1, label_x=1000000001.0, gap=0), "magnitude above 1e9"),
                    (dict(anchors=[(0, 0)], height=1, label_x=1e9, gap=0), "must be within"),
                    (dict(anchors=[(0, 0)], height=1, label_x=999999999, gap=0), "must be within"),
                    (dict(anchors=[(0, 0)], height=1, label_x=float("nan"), gap=0), "finite")]:
        with pytest.raises(ValueError, match=msg):
            L(**kw)

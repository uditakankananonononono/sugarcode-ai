from itertools import permutations
import pytest
from sugarcode.extra_doc import logistics_route as lr

T = lr.best_tour


def test_constants():
    assert (lr.MAX_STOPS, lr.MAX_COST) == (12, 1_000_000)
    assert lr.STATUS_NOTE.startswith("PARTIAL") and "no time windows" in lr.STATUS_NOTE


def test_hand_literals():
    r = T([[0, 5], [7, 0]])
    assert r["cost"] == 12 and r["order"] == [0, 1, 0] and r["stops"] == 2
    sq = [[0, 1, 9, 1], [1, 0, 1, 9], [9, 1, 0, 1], [1, 9, 1, 0]]    # ring 0-1-2-3-0, each hop costs 1
    r = T(sq)
    assert r["cost"] == 4 and r["order"] == [0, 1, 2, 3, 0]            # the reverse ring 0-3-2-1-0 also costs 4
    d3 = [[0, 2, 9], [1, 0, 6], [3, 5, 0]]                              # asymmetric: 0-1-2-0 = 2+6+3 = 11, 0-2-1-0 = 9+5+1 = 15
    assert T(d3)["cost"] == 11 and T(d3)["order"] == [0, 1, 2, 0]
    z = [[0] * 4 for _ in range(4)]
    assert T(z)["cost"] == 0 and T(z)["order"] == [0, 1, 2, 3, 0]      # all ties: lexicographically smallest
    d = [[0, 10, 1], [10, 0, 1], [1, 1, 0]]
    assert T(d)["cost"] == 12 and T(d)["order"] == [0, 1, 2, 0]        # 10 + 1 + 1 both ways: smaller order wins
    diag = [[99, 4], [4, 77]]
    assert T(diag)["cost"] == 8                                          # the diagonal is ignored
    assert T([[0, 0], [0, 0]])["order"] == [0, 1, 0]


def test_oracle_random():
    import random
    rnd = random.Random(55)
    for _ in range(150):
        n = rnd.randint(2, 7)
        d = [[rnd.randint(0, 9) for _ in range(n)] for _ in range(n)]
        best = None
        for p in permutations(range(1, n)):                    # brute force over every tour, ties by sequence
            tour = [0, *p, 0]
            c = sum(d[a][b] for a, b in zip(tour, tour[1:]))
            if best is None or (c, tour) < best:
                best = (c, tour)
        r = T(d)
        assert (r["cost"], r["order"]) == best


def test_max_size_runs():
    n = 12
    d = [[abs(i - j) * 3 + (i * j) % 5 for j in range(n)] for i in range(n)]
    r = T(d)
    assert sorted(r["order"][1:-1]) == list(range(1, n)) and r["order"][0] == r["order"][-1] == 0
    assert r["cost"] == sum(d[a][b] for a, b in zip(r["order"], r["order"][1:]))
    assert r["cost"] <= sum(d[i][i + 1] for i in range(n - 1)) + d[n - 1][0]


def test_boundaries_and_messages():
    with pytest.raises(ValueError, match="dist: list required"):
        T("ab")
    with pytest.raises(ValueError, match="dist: 2 to 12 stops required"):
        T([[0]])
    with pytest.raises(ValueError, match="dist: 2 to 12 stops required"):
        T([[0] * 13 for _ in range(13)])
    with pytest.raises(ValueError, match=r"dist\[1\]: list required"):
        T([[0, 1], "ab"])
    with pytest.raises(ValueError, match=r"dist\[1\]: 2 entries required"):
        T([[0, 1], [1]])
    with pytest.raises(ValueError, match=r"dist\[0\]: 2 entries required"):
        T([[0, 1, 2], [1, 0, 1]])
    for bad in (True, 1.0, "1"):
        with pytest.raises(ValueError, match=r"dist\[1\]\[0\]: integer required"):
            T([[0, 1], [bad, 0]])
    for bad in (-1, 1_000_001):
        with pytest.raises(ValueError, match=r"dist\[0\]\[1\]: must be within 0 to 1000000"):
            T([[0, bad], [1, 0]])
    assert T([[0, 1_000_000], [1_000_000, 0]])["cost"] == 2_000_000
    # the matrix size is checked before any entry is read
    with pytest.raises(ValueError, match="dist: 2 to 12 stops required"):
        T([["x"]] * 13)

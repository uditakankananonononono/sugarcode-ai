import copy
import random
from fractions import Fraction

import pytest

from sugarcode.extra_doc import simulation_engine as m
from sugarcode.extra_doc.simulation_engine import SimError, simulation_engine as run

F = Fraction
KEYS = "data keys must be exactly customers, servers"


def d(cust=((0, 5), (1, 3), (2, 4), (10, 2)), k=1):
    return {"customers": [list(c) for c in cust], "servers": k}


def bad(data, msg):
    with pytest.raises(SimError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: advance a clock one unit at a time; servers are 'busy until' timers."""
    cust = data["customers"]
    k = data["servers"]
    busy_until = [0] * k
    idle_since = [0] * k
    queue = []
    start = {}
    server = {}
    t = 0
    nxt = 0
    done = 0
    while done < len(cust):
        while nxt < len(cust) and cust[nxt][0] == t:
            queue.append(nxt)
            nxt += 1
        for j in range(k):
            if busy_until[j] <= t:
                idle_since[j] = max(idle_since[j], busy_until[j])
        while queue:
            idle = [j for j in range(k) if busy_until[j] <= t]
            if not idle:
                break
            j = min(idle, key=lambda x: (idle_since[x], x))
            i = queue.pop(0)
            start[i], server[i] = t, j
            busy_until[j] = t + cust[i][1]
            idle_since[j] = busy_until[j]
            done += 1
        t += 1
    rows = [{"server": server[i], "arrival": cust[i][0], "start": start[i], "finish": start[i] + cust[i][1],
             "wait": start[i] - cust[i][0]} for i in range(len(cust))]
    return rows


def check(data):
    out = run(data)
    rows = oracle(data)
    assert out["customers"] == rows
    k = data["servers"]
    busy = [sum(c[1] for i, c in enumerate(data["customers"]) if rows[i]["server"] == j) for j in range(k)]
    assert out["busy_time"] == busy
    ms = max(r["finish"] for r in rows)
    assert out["makespan"] == ms
    waits = [r["wait"] for r in rows]
    assert F(out["average_wait"]) == F(sum(waits), len(waits)) and out["max_wait"] == max(waits)
    assert F(out["utilisation"]) == F(sum(busy), k * ms)
    peak = max(sum(1 for j in range(i + 1) if rows[j]["start"] > rows[i]["arrival"]) for i in range(len(rows)))
    assert out["max_queue_length"] == peak
    return out


def test_hand_worked_single_server():
    out = run(d())
    assert out["customers"] == [
        {"server": 0, "arrival": 0, "start": 0, "finish": 5, "wait": 0},
        {"server": 0, "arrival": 1, "start": 5, "finish": 8, "wait": 4},
        {"server": 0, "arrival": 2, "start": 8, "finish": 12, "wait": 6},
        {"server": 0, "arrival": 10, "start": 12, "finish": 14, "wait": 2},
    ]
    assert out["makespan"] == 14 and out["busy_time"] == [14] and out["utilisation"] == "1"
    assert out["average_wait"] == "3" and out["max_wait"] == 6
    assert out["max_queue_length"] == 2        # at arrival 2: customers 1 and 2 have arrived and not started
    assert out["status"] == "completed"
    assert out["claims"] == {"models_real_system": False, "generalises": False, "capacity_adequate": False, "real_world": False}
    assert len(out["not_claimed"]) == 4
    check(d())


def test_two_servers_earliest_free_with_lowest_index_ties():
    out = check(d([(0, 10), (0, 3), (1, 1), (4, 2)], 2))
    assert [r["server"] for r in out["customers"]] == [0, 1, 1, 1]
    # server 0 free at 20 vs server 1 free at 5: the earliest-free server is taken, not the lowest index
    out = check(d([(0, 20), (0, 5), (25, 1)], 2))
    out = check(d([(0, 5), (0, 3), (10, 1)], 2))
    assert out["customers"][2]["server"] == 1       # free since 8 vs 5: server 0 became free earlier
    assert out["customers"][2]["start"] == 10 and out["customers"][2]["wait"] == 0
    out = check(d([(0, 5), (0, 5), (10, 1)], 2))
    assert out["customers"][2]["server"] == 0       # both free at 5: tie goes to the lowest index


def test_idle_gap_and_utilisation_fraction():
    out = check(d([(0, 2), (10, 2)], 1))
    assert out["makespan"] == 12 and out["utilisation"] == "1/3" and out["average_wait"] == "0"
    assert out["max_wait"] == 0 and out["max_queue_length"] == 0
    out = check(d([(5, 1)], 4))
    assert out["makespan"] == 6 and out["utilisation"] == "1/24" and out["busy_time"] == [1, 0, 0, 0]


def test_simultaneous_arrivals_keep_input_order():
    out = check(d([(0, 4), (0, 4), (0, 4)], 1))
    assert [r["start"] for r in out["customers"]] == [0, 4, 8]
    assert out["max_queue_length"] == 2 and out["average_wait"] == "4"


def test_random_against_oracle():
    rng = random.Random(51)
    for _ in range(300):
        n = rng.randint(1, 12)
        t = 0
        cust = []
        for _ in range(n):
            t += rng.randint(0, 6)
            cust.append((t, rng.randint(1, 9)))
        check(d(cust, rng.randint(1, 4)))


def test_caps_and_boundaries():
    run(d([(1000000, 10000)] * 200, 4))
    run(d([(1000000, 10000)], 1))
    bad(d([(1000001, 1)]), "arrival out of range")
    bad(d([(0, 10001)]), "service out of range")
    bad(d([(0, 0)]), "service out of range")
    bad(d([(-1, 1)]), "arrival out of range")
    bad(d([(0, 1)] * 201), "customers must be a list of 1..200 [arrival, service] pairs")
    bad(d([(0, 1)] * 10**5), "customers must be a list of 1..200 [arrival, service] pairs")
    bad(d([]), "customers must be a list of 1..200 [arrival, service] pairs")
    bad(d([(5, 1), (4, 1)]), "arrivals must be non-decreasing")
    run(d([(5, 1), (5, 1)]))
    bad(d(k=5), "servers out of range")
    bad(d(k=0), "servers out of range")
    bad(d(k=-1), "servers out of range")


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint_slots(v):
    bad(d(k=v), "servers must be an int")
    x = d()
    x["customers"] = [[v, 1]]
    bad(x, "arrival must be an int")
    x["customers"] = [[0, v]]
    bad(x, "service must be an int")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a", "b")])
def test_noncontainer(v):
    x = d()
    x["customers"] = v
    bad(x, "customers must be a list of 1..200 [arrival, service] pairs")
    x["customers"] = [v]
    bad(x, "customer must be an [arrival, service] pair")
    for c in ([1], [1, 2, 3]):
        x["customers"] = [c]
        bad(x, "customer must be an [arrival, service] pair")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("servers", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("customers", "servers"):
        x = d()
        del x[k]
        bad(x, KEYS)
        x["other"] = 1
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["customers"][0]["start"] = 99
    a["busy_time"].append(1)
    r = run(x)
    assert r["claims"]["real_world"] is False and r["customers"][0]["start"] == 0 and len(r["busy_time"]) == 1
    assert m.CLAIMS["real_world"] is False


class _SubInt(int):
    pass


class _Quirky(int):
    """int subclass with lying arithmetic and comparisons."""
    def __sub__(self, o):
        return 0

    def __add__(self, o):
        return 1

    def __mul__(self, o):
        return 0

    def __gt__(self, o):
        return False

    def __lt__(self, o):
        return False


def _int_paths(x, path=()):
    if type(x) is int:
        yield path
    elif isinstance(x, dict):
        for k in x:
            yield from _int_paths(x[k], path + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _int_paths(v, path + (i,))


def _put(x, path, val):
    y = copy.deepcopy(x)
    t = y
    for k in path[:-1]:
        t = t[k]
    t[path[-1]] = val
    return y


def test_int_subclasses_refused_in_every_int_slot():
    base = d()
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(SimError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x

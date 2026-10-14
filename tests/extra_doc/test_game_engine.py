import copy
import random

import pytest

from sugarcode.extra_doc import game_engine as m
from sugarcode.extra_doc.game_engine import GameError, game_engine as run

KEYS = "data keys must be exactly grid, moves"


def d(grid=("@.o", ".#G"), moves=""):
    return {"grid": list(grid), "moves": moves}


def bad(data, msg):
    with pytest.raises(GameError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(grid, moves):
    """Independent: complex-plane coordinates, sets for walls/coins, explicit stop flag."""
    walls, coins, goal, pos = set(), set(), None, None
    for i, row in enumerate(grid):
        for j, ch in enumerate(row):
            z = complex(j, i)
            if ch == "#":
                walls.add(z)
            elif ch == "o":
                coins.add(z)
            elif ch == "G":
                goal = z
            elif ch == "@":
                pos = z
    step = {"U": -1j, "D": 1j, "L": -1, "R": 1}
    w, h = len(grid[0]), len(grid)
    got = blk = app = 0
    stopped_at = None
    for k, c in enumerate(moves):
        t = pos + step[c]
        app += 1
        if t in walls or not (0 <= t.real < w and 0 <= t.imag < h):
            blk += 1
            continue
        pos = t
        if pos in coins:
            coins.remove(pos)
            got += 1
        if pos == goal:
            stopped_at = k
            break
    ign = 0 if stopped_at is None else len(moves) - stopped_at - 1
    return (int(pos.imag), int(pos.real), got, len(coins), app, blk, ign, stopped_at is not None)


def check(grid, moves):
    o = run(d(grid, moves))
    got = (o["row"], o["column"], o["coins_collected"], o["coins_left"], o["moves_applied"], o["blocked"], o["ignored"], o["goal_reached"])
    assert got == oracle(grid, moves)
    return o


def test_hand_worked():
    o = run(d(moves="RRDL"))
    # R->(0,1) R->(0,2) coin D->(1,2) goal, L ignored
    assert (o["row"], o["column"], o["coins_collected"], o["coins_left"]) == (1, 2, 1, 0)
    assert (o["moves_applied"], o["blocked"], o["ignored"], o["goal_reached"]) == (3, 0, 1, True)
    assert o["status"] == "completed"
    assert o["claims"] == {"fun": False, "good_strategy": False, "general_rules": False, "real_product": False}
    assert len(o["not_claimed"]) == 4
    check(("@.o", ".#G"), "RRDL")


def test_blocking_and_edges():
    o = run(d(moves="UL"))
    assert (o["row"], o["column"], o["blocked"], o["moves_applied"], o["ignored"]) == (0, 0, 2, 2, 0)
    o = run(d(moves="DR"))
    assert (o["row"], o["column"], o["blocked"]) == (1, 0, 1)    # D ok, R into wall
    o = run(d(moves="DDDD"))
    assert o["blocked"] == 3
    o = run(d(moves="RRRR"))
    assert o["blocked"] == 2 and o["coins_collected"] == 1
    o = run(d(moves=""))
    assert (o["row"], o["column"], o["coins_left"], o["moves_applied"], o["goal_reached"]) == (0, 0, 1, 0, False)


def test_coin_collected_once():
    o = run(d(("@o.",), "RLRL"))
    assert o["coins_collected"] == 1 and o["coins_left"] == 0 and o["row"] == 0 and o["column"] == 0


def test_no_goal_grid_and_start_not_a_wall():
    o = run(d(("o@o",), "LRR"))
    assert o["coins_collected"] == 2 and o["goal_reached"] is False
    o = run(d(("@",), "UDLR"))
    assert o["blocked"] == 4 and o["coins_left"] == 0


def test_random_against_oracle():
    rng = random.Random(60)
    for _ in range(400):
        h, w = rng.randint(1, 6), rng.randint(1, 6)
        cells = [[rng.choice("..#o") for _ in range(w)] for _ in range(h)]
        pos = [(i, j) for i in range(h) for j in range(w)]
        rng.shuffle(pos)
        i, j = pos.pop()
        cells[i][j] = "@"
        if pos and rng.random() < 0.7:
            i, j = pos.pop()
            cells[i][j] = "G"
        grid = ["".join(r) for r in cells]
        check(grid, "".join(rng.choice("UDLR") for _ in range(rng.randint(0, 30))))


def test_caps_and_boundaries():
    row = "@" + "." * 19
    run(d([row] + ["." * 20] * 19, "U" * 500))
    bad(d([row] + ["." * 20] * 20, ""), "grid must be a list of 1..20 strings")
    bad(d([row + "."], ""), "grid width must be 1..20")
    bad(d([""], ""), "grid width must be 1..20")
    bad(d([], ""), "grid must be a list of 1..20 strings")
    bad(d(["@"] * 10**5, ""), "grid must be a list of 1..20 strings")
    bad(d(["@"], "U" * 501), "moves too long")
    bad(d(["@"], "U" * 10**6), "moves too long")
    bad(d(["@.", "."], ""), "grid rows must have equal length")
    bad(d(["@x"], ""), "grid has an unknown cell character")
    bad(d(["@.", ".x"], ""), "grid has an unknown cell character")
    bad(d(["..", ".."], ""), "grid must have exactly one start")
    bad(d(["@@"], ""), "grid must have exactly one start")
    bad(d(["@GG"], ""), "grid must have at most one goal")
    bad(d(["@G", "G."], ""), "grid must have at most one goal")
    run(d(["@G"], ""))
    bad(d(["@"], "UX"), "moves must use only U D L R")
    bad(d(["@"], "u"), "moves must use only U D L R")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",), [1], [None]])
def test_bad_types(v):
    x = d()
    x["grid"] = v
    bad(x, "grid must be a list of 1..20 strings" if not isinstance(v, list) else "grid rows must be strings")
    x = d()
    x["moves"] = v
    if v == "ab":
        bad(x, "moves must use only U D L R")
    else:
        bad(x, "moves must be a string")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("grid", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("grid", "moves"):
        x = d()
        del x[k]
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d(moves="RRDL")
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["fun"] = True
    a["not_claimed"].append("x")
    r = run(x)
    assert r["claims"]["fun"] is False and len(r["not_claimed"]) == 4 and m.CLAIMS["fun"] is False


def test_width_checked_on_first_row():
    bad(d(["", "@...."], ""), "grid width must be 1..20")
    bad(d(["@" + "." * 20, "@"], ""), "grid width must be 1..20")
    bad(d(["@", "." * 21], ""), "grid rows must have equal length")


class _SubStr(str):
    pass


class _LyingStr(str):
    """str subclass that hashes like 1 and equals 1."""
    def __hash__(self):
        return 1

    def __eq__(self, o):
        return o == 1 or str.__eq__(self, o)


def _variants(x):
    """Yield every copy of x with one str leaf or one dict key replaced by bytes or a str subclass."""
    import copy as _c
    def walk(node, path):
        if type(node) is str:
            yield path, "leaf"
        elif isinstance(node, dict):
            for k in node:
                if type(k) is str:
                    yield path + (k,), "key"
                yield from walk(node[k], path + (k,))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, path + (i,))
    for path, kind in walk(x, ()):
        for mk in (lambda s: s.encode(), _SubStr, _LyingStr):
            if kind == "key" and mk is _SubStr:
                continue   # a plain str subclass hashes and compares like its key: indistinguishable as a dict key
            y = _c.deepcopy(x)
            t = y
            for k in path[:-1]:
                t = t[k]
            last = path[-1]
            if kind == "leaf":
                t[last] = mk(t[last])
            else:
                t2 = {}
                for k, v in t.items():
                    t2[mk(k) if k == last else k] = v
                if len(path) == 1:
                    y = t2
                else:
                    u = y
                    for k in path[:-2]:
                        u = u[k]
                    u[path[-2]] = t2
            yield y


def test_nonexact_str_refused_in_every_str_slot_and_key():
    base = d(moves="RRDL")
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(GameError):
            run(y)
    assert n >= 4

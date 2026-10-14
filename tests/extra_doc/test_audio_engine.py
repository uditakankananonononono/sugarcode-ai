import copy
import math
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import audio_engine as m
from sugarcode.extra_doc.audio_engine import AudioError, audio_engine as run

KEYS = "data keys must be exactly gains, tracks"
SHAPE = "gains must be a list with one [num, den] pair per track"


def d(tracks=None, gains=None):
    tracks = [[100, -200, 300]] if tracks is None else tracks
    gains = [[1, 1]] * len(tracks) if gains is None else gains
    return {"tracks": tracks, "gains": gains}


def bad(data, msg):
    with pytest.raises(AudioError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: integer arithmetic over the lcm of the gain denominators (no Fraction)."""
    tr, gn = data["tracks"], data["gains"]
    L = 1
    for _, den in gn:
        L = L * den // math.gcd(L, den)
    n = max(len(t) for t in tr)
    out, clip = [], 0
    for i in range(n):
        num = sum(g[0] * (L // g[1]) * (t[i] if i < len(t) else 0) for t, g in zip(tr, gn))
        r = (2 * num + L) // (2 * L)
        c = r
        if c > 32767:
            c = 32767
        if c < -32768:
            c = -32768
        clip += c != r
        out.append(c)
    en = sum(s * s for s in out)
    return out, clip, max(abs(s) for s in out), en, F(en, n)


def check(data):
    o = run(data)
    s, c, p, e, mp = oracle(data)
    assert (o["samples"], o["clipped"], o["peak"], o["energy"], F(o["mean_power"]), o["length"]) == (s, c, p, e, mp, len(s))
    return o


def test_hand_worked():
    o = run(d([[100, -200, 300], [10, 10]], [[1, 2], [-1, 1]]))
    # 50-10=40 ; -100-10=-110 ; 150-0=150
    assert o["samples"] == [40, -110, 150] and o["length"] == 3
    assert (o["clipped"], o["peak"], o["energy"], o["mean_power"]) == (0, 150, 1600 + 12100 + 22500, "36200/3")
    assert o["status"] == "completed"
    assert o["claims"] == {"sounds_good": False, "gains_suitable": False, "real_audio": False, "real_world": False}
    assert len(o["not_claimed"]) == 4


def test_rounding_half_up_both_signs():
    # 1/2*1 = 0.5 -> 1 ; 1/2*(-1) = -0.5 -> 0 ; 1/2*3=1.5 -> 2 ; 1/2*(-3) = -1.5 -> -1 ; 1/3*1 -> 0 ; 2/3*1 -> 1
    o = check(d([[1, -1, 3, -3]], [[1, 2]]))
    assert o["samples"] == [1, 0, 2, -1]
    assert check(d([[1]], [[1, 3]]))["samples"] == [0]
    assert check(d([[1]], [[2, 3]]))["samples"] == [1]
    assert check(d([[-1]], [[1, 3]]))["samples"] == [0]
    assert check(d([[-1]], [[2, 3]]))["samples"] == [-1]


def test_clipping_boundaries():
    o = run(d([[32767, -32768, 32766, -32767]], [[1, 1]]))
    assert o["clipped"] == 0 and o["samples"] == [32767, -32768, 32766, -32767]
    o = run(d([[32767, -32768]], [[2, 1]]))
    assert o["samples"] == [32767, -32768] and o["clipped"] == 2 and o["peak"] == 32768
    o = run(d([[16384, -16385]], [[2, 1]]))
    assert o["samples"] == [32767, -32768] and o["clipped"] == 2     # 32768 clips, -32770 clips
    o = run(d([[16383, -16384]], [[2, 1]]))
    assert o["samples"] == [32766, -32768] and o["clipped"] == 0
    o = run(d([[32767], [1]], [[1, 1], [1, 1]]))
    assert o["samples"] == [32767] and o["clipped"] == 1


def test_negative_and_zero_gain_and_pad():
    o = check(d([[5, 5, 5], [7]], [[0, 7], [-2, 1]]))
    assert o["samples"] == [-14, 0, 0] and o["peak"] == 14
    o = check(d([[0]]))
    assert o["samples"] == [0] and o["peak"] == 0 and o["mean_power"] == "0"


def test_random_against_oracle():
    rng = random.Random(79)
    for _ in range(300):
        k = rng.randint(1, 4)
        tr = [[rng.choice([rng.randint(-40000 // 2, 16383), rng.randint(-5, 5), 32767, -32768]) for _ in range(rng.randint(1, 6))] for _ in range(k)]
        tr = [[max(-32768, min(32767, s)) for s in t] for t in tr]
        gn = [[rng.randint(-100, 100), rng.randint(1, 100)] for _ in range(k)]
        check(d(tr, gn))


def test_caps_and_ranges():
    run(d([[1] * 1000] * 8))
    bad(d([[1]] * 9), "tracks must be a list of 1..8 tracks")
    bad(d([[1]] * 10**5), "tracks must be a list of 1..8 tracks")
    bad({"tracks": [], "gains": []}, "tracks must be a list of 1..8 tracks")
    bad(d([[1] * 1001]), "each track must be a list of 1..1000 samples")
    bad(d([[1] * 10**6]), "each track must be a list of 1..1000 samples")
    bad(d([[]]), "each track must be a list of 1..1000 samples")
    bad(d([[32768]]), "sample out of range")
    bad(d([[-32769]]), "sample out of range")
    run(d([[-32768, 32767]]))
    bad(d(gains=[[101, 1]]), "gain numerator out of range")
    bad(d(gains=[[-101, 1]]), "gain numerator out of range")
    run(d(gains=[[100, 100]]))
    run(d(gains=[[-100, 1]]))
    bad(d(gains=[[1, 0]]), "gain denominator out of range")
    bad(d(gains=[[1, 101]]), "gain denominator out of range")
    bad(d(gains=[[1, -1]]), "gain denominator out of range")
    bad(d(gains=[[1, 1], [1, 1]]), SHAPE)
    bad({"tracks": [[1]], "gains": []}, SHAPE)


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(v):
    bad(d([[v]]), "sample must be an int")
    bad(d(gains=[[v, 1]]), "gain numerator must be an int")
    bad(d(gains=[[1, v]]), "gain denominator must be an int")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainers(v):
    x = d()
    x["tracks"] = v
    bad(x, "tracks must be a list of 1..8 tracks")
    x = d()
    x["tracks"] = [v]
    x["gains"] = [[1, 1]]
    bad(x, "each track must be a list of 1..1000 samples")
    x = d()
    x["gains"] = v
    bad(x, SHAPE)
    x["gains"] = [v]
    bad(x, SHAPE)
    for g in ([1], [1, 1, 1]):
        x["gains"] = [g]
        bad(x, SHAPE)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("tracks", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("tracks", "gains"):
        x = d()
        del x[k]
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d([[100, -200], [3]], [[1, 2], [3, 4]])
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["samples"].append(1)
    r = run(x)
    assert r["claims"]["real_world"] is False and len(r["samples"]) == 2 and m.CLAIMS["real_world"] is False


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
            with pytest.raises(AudioError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x

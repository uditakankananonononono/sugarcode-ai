import re
import itertools
import pytest
from sugarcode.extra_doc import limit_gate as lg

G = lg.gate
NC = ("what a request is", "whether a refusal is appropriate", "protection of any resource",
      "how a refusal is communicated", "fairness of the order")
BM = "budget: whole number 0 to 10000 required"
RM = "requests: tuple of 0 to 50 whole numbers required"


class I(int):
    pass


class Tu(tuple):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        G(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def oracle(budget, reqs):                 # independent: subset-by-position simulation via a running total list
    acc, ref, used = [], [], 0
    for i, c in enumerate(reqs):
        if used + c <= budget:
            used += c
            acc.append(i)
        else:
            ref.append(i)
    return tuple(acc), tuple(ref), budget - used


def test_constants():
    assert lg.MAX_BUDGET == 10000 and lg.MAX_REQUESTS == 50 and lg.NOT_CLAIMED == NC


def test_literals():
    assert G(10, (4, 7, 6, 1)) == {"accepted": (0, 2), "refused": (1, 3), "remaining": 0,
                                   "limit_gate_validated": False, "not_claimed": NC}
    assert G(0, ()) == {"accepted": (), "refused": (), "remaining": 0, "limit_gate_validated": False, "not_claimed": NC}
    assert G(5, (5,))["accepted"] == (0,) and G(5, (6,))["refused"] == (0,)
    assert G(0, (1,))["refused"] == (0,)
    assert G(10000, (10000,))["remaining"] == 0


def test_exhaustive_oracle():
    for b in range(0, 8):
        for n in range(0, 4):
            for reqs in itertools.product(range(1, 6), repeat=n):
                r = G(b, reqs)
                a, f, left = oracle(b, reqs)
                assert (r["accepted"], r["refused"], r["remaining"]) == (a, f, left)


def test_caps():
    assert G(10000, (1,) * 50)["remaining"] == 9950
    refuse(RM, 5, (1,) * 51)
    refuse("requests[0]: whole number 1 to 10000 required", 5, (10001,))
    assert G(10000, (10000, 1))["refused"] == (1,)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), -1, 10001])
def test_budget(bad):
    refuse(BM, bad, ())


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), 0, -1, 10001])
def test_cost(bad):
    refuse("requests[0]: whole number 1 to 10000 required", 5, (bad,))
    refuse("requests[2]: whole number 1 to 10000 required", 5, (1, 2, bad))


@pytest.mark.parametrize("bad", [[], [1], None, "1", 5, Tu((1,))])
def test_requests_shape(bad):
    refuse(RM, 5, bad)


def test_order():
    refuse(BM, None, None)
    refuse(RM, 5, (1,) * 51 + (0,))
    refuse("requests[1]: whole number 1 to 10000 required", 5, (1, 0, 0))

    assert G(10, (4, 7, 1))["accepted"] == (0, 2) and G(10, (4, 7, 1))["remaining"] == 5

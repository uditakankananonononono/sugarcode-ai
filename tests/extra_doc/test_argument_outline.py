import itertools
import re
import pytest
from sugarcode.extra_doc import argument_outline as ao

C = ao.check
NC = ("persuasive effect", "truth or fairness of the content", "quality of the writing",
      "audience response", "runtime behaviour")
LB = "one of claim, evidence, counter, rebuttal, call required"
LABELS = ("claim", "evidence", "counter", "rebuttal", "call")


class Li(list):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        C(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def oracle(o):                              # independent: scan every position with explicit neighbour lookups
    n, out = len(o), []
    for i, x in enumerate(o):
        if i == 0 and x != "claim":
            out.append((i, "opening_not_claim"))
        if i == n - 1 and x != "call":
            out.append((i, "closing_not_call"))
        if x == "call" and i < n - 1:
            out.append((i, "call_before_end"))
        if x == "claim":
            j, found = i + 1, False
            while j < n and o[j] != "claim":
                found = found or o[j] == "evidence"
                j += 1
            if not found:
                out.append((i, "claim_without_evidence"))
        if x == "counter" and not (i + 1 < n and o[i + 1] == "rebuttal"):
            out.append((i, "counter_without_rebuttal"))
        if x == "rebuttal" and not (i > 0 and o[i - 1] == "counter"):
            out.append((i, "rebuttal_without_counter"))
    return sorted(out)


def test_constants():
    assert ao.MAX_LABELS == 50 and ao.LABELS == LABELS and ao.NOT_CLAIMED == NC


def test_hand_literals():
    good = ["claim", "evidence", "counter", "rebuttal", "call"]
    assert C(good)["issues"] == [] and C(good)["structure_complete"] is True
    assert C(["evidence", "call"])["issues"] == [(0, "opening_not_claim")]
    assert C(["claim", "evidence"])["issues"] == [(1, "closing_not_call")]
    assert C(["claim", "call", "evidence", "call"])["issues"] == [(1, "call_before_end")]   # later evidence still counts
    assert C(["claim", "call"])["issues"] == [(0, "claim_without_evidence")]
    assert C(["claim", "evidence", "claim", "call"])["issues"] == [(2, "claim_without_evidence")]
    assert C(["claim", "evidence", "counter", "call"])["issues"] == [(2, "counter_without_rebuttal")]
    assert C(["claim", "evidence", "rebuttal", "call"])["issues"] == [(2, "rebuttal_without_counter")]
    assert C(["rebuttal"])["issues"] == [(0, "closing_not_call"), (0, "opening_not_claim"),
                                         (0, "rebuttal_without_counter")]
    assert C(["claim", "evidence", "counter", "rebuttal", "rebuttal", "call"])["issues"] == [(4, "rebuttal_without_counter")]
    assert C(["claim", "counter"])["issues"] == [(0, "claim_without_evidence"), (1, "closing_not_call"),
                                                 (1, "counter_without_rebuttal")]
    assert C(["claim", "counter", "rebuttal", "evidence", "call"])["issues"] == []


def test_shape_and_untouched():
    o = ["claim", "evidence", "call"]
    r = C(o)
    assert o == ["claim", "evidence", "call"]
    assert r == {"issues": [], "structure_complete": True, "writing_validated": False, "not_claimed": NC}


def test_exhaustive_against_oracle():
    for n in range(1, 7):
        for o in itertools.product(LABELS, repeat=n):
            assert C(list(o))["issues"] == oracle(list(o)), o


def test_caps_accepted():
    o = ["claim"] + ["evidence"] * 48 + ["call"]
    assert C(o)["issues"] == [] and len(o) == 50
    assert len(C(["call"] * 50)["issues"]) == 50


@pytest.mark.parametrize("bad", [None, 1, "", "Claim", "CLAIM", "claim ", "call\n", "cl\u0430im", "evidence\u200b",
                                 St("claim"), b"claim", ["claim"]])
def test_label_refusals(bad):
    refuse(f"outline[0]: {LB}", [bad])
    refuse(f"outline[1]: {LB}", ["claim", bad])
    refuse(f"outline[2]: {LB}", ["claim", "call", bad])


@pytest.mark.parametrize("bad", [(), None, "claim", Li(["claim"]), [], ["claim"] * 51])
def test_outline_shape(bad):
    refuse("outline: list of 1 to 50 required", bad)


def test_check_order():
    refuse("outline: list of 1 to 50 required", None)
    refuse(f"outline[0]: {LB}", [None, 5])

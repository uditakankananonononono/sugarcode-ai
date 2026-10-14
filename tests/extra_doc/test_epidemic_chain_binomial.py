import copy
import itertools
from fractions import Fraction

import pytest

from sugarcode.extra_doc import epidemic_chain_binomial as m
from sugarcode.extra_doc.epidemic_chain_binomial import EpidemicError, epidemic_chain_binomial as run

KEYS = "data keys must be exactly susceptible, infected, p_num, p_den"
LITERAL_NOT_CLAIMED = [
    "the model describes a real disease or population",
    "the contact probability is right",
    "the outcome predicts anything",
    "real-world outcome",
]


def d(s, i, num, den):
    return {"susceptible": s, "infected": i, "p_num": num, "p_den": den}


def bad(data, msg):
    with pytest.raises(EpidemicError) as e:
        run(data)
    assert str(e.value) == msg


def enumerate_oracle(s0, i0, p):
    # every susceptible is infected independently with probability 1 - q^I; enumerate all subsets
    q = 1 - p
    final = {}
    gens = Fraction(0)
    exp_i = {}

    def go(s, i, prob, t):
        nonlocal gens
        exp_i[t] = exp_i.get(t, Fraction(0)) + prob * i
        if i == 0:
            final[s0 - s] = final.get(s0 - s, Fraction(0)) + prob
            return
        gens += prob
        inf = 1 - q ** i
        for pick in itertools.product((0, 1), repeat=s):
            k = sum(pick)
            go(s - k, k, prob * inf ** k * (1 - inf) ** (s - k), t + 1)

    go(s0, i0, Fraction(1), 0)
    return [final.get(k, Fraction(0)) for k in range(s0 + 1)], gens, exp_i


def test_hand_case_two_susceptibles():
    out = run(d(2, 1, 1, 2))
    assert out["final_size_distribution"] == ["1/4", "1/4", "1/2"]
    assert out["mean_final_size"] == "5/4" and out["no_spread_probability"] == "1/4"
    assert out["expected_generations"] == "2"
    assert out["expected_infectives_by_generation"] == ["1", "1", "1/4", "0"]


def test_certain_contact_infects_everyone_in_one_generation():
    out = run(d(5, 2, 1, 1))
    assert out["final_size_distribution"] == ["0"] * 5 + ["1"]
    assert out["mean_final_size"] == "5" and out["no_spread_probability"] == "0"
    assert out["expected_generations"] == "2"
    assert out["expected_infectives_by_generation"] == ["2", "5", "0", "0", "0", "0", "0"][:7]


def test_single_susceptible_formula():
    # one susceptible, I infectives, p = 1/3: infected with prob 1 - (2/3)^I
    out = run(d(1, 3, 1, 3))
    assert out["final_size_distribution"] == ["8/27", "19/27"]
    assert out["no_spread_probability"] == "8/27" and out["mean_final_size"] == "19/27"


def test_matches_subset_enumeration_oracle():
    for s0, i0, num, den in ((3, 1, 1, 3), (4, 2, 1, 4), (5, 1, 2, 5), (4, 3, 1, 2), (5, 2, 1, 10), (3, 5, 7, 8)):
        out = run(d(s0, i0, num, den))
        final, gens, exp_i = enumerate_oracle(s0, i0, Fraction(num, den))
        assert out["final_size_distribution"] == [str(x) for x in final], (s0, i0, num, den)
        assert out["expected_generations"] == str(gens)
        got = [Fraction(x) for x in out["expected_infectives_by_generation"]]
        assert got == [exp_i.get(t, Fraction(0)) for t in range(len(got))]
        assert len(got) == s0 + 2


def test_distribution_sums_to_one_at_the_caps():
    out = run(d(12, 12, 999, 1000))
    assert sum(Fraction(x) for x in out["final_size_distribution"]) == 1
    out = run(d(12, 1, 1, 1000))
    dist = [Fraction(x) for x in out["final_size_distribution"]]
    assert sum(dist) == 1 and dist[0] > Fraction(9, 10)
    assert Fraction(out["mean_final_size"]) == sum(k * x for k, x in enumerate(dist))


def test_more_contact_probability_never_lowers_mean_size():
    means = [Fraction(run(d(6, 1, n, 20))["mean_final_size"]) for n in range(1, 21)]
    assert means == sorted(means)


def test_claims_and_input_not_mutated():
    data = d(3, 1, 1, 2)
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"describes_real_disease": False, "probability_right": False, "predictive": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    out["final_size_distribution"][0] = "9"
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert again["final_size_distribution"][0] != "9"
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MAX_S, m.MAX_I, m.MAX_DEN) == (12, 12, 1000)


def test_refusals_and_caps():
    for x in (None, [], {"susceptible": 1}, dict(d(2, 1, 1, 2), extra=1)):
        bad(x, KEYS)
    for name in ("susceptible", "infected", "p_num", "p_den"):
        for v in (True, 1.0, "1", None):
            bad(dict(d(2, 1, 1, 2), **{name: v}), f"{name} must be an int")
    bad(d(0, 1, 1, 2), "susceptible out of range")
    bad(d(13, 1, 1, 2), "susceptible out of range")
    bad(d(2, 0, 1, 2), "infected out of range")
    bad(d(2, 13, 1, 2), "infected out of range")
    bad(d(2, 1, 0, 2), "p_num out of range")
    bad(d(2, 1, 3, 2), "p_num out of range")
    bad(d(2, 1, 1, 0), "p_den out of range")
    bad(d(2, 1, 1, 1001), "p_den out of range")
    run(d(1, 1, 1, 1))
    run(d(12, 12, 1000, 1000))
    run(d(12, 12, 1, 1000))
    run(d(2, 1, 2, 2))

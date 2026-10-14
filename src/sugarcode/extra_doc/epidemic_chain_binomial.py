"""Epidemic Modeling - exact Reed-Frost chain-binomial outcome distribution.

Pure function over caller data. No retrieval, no network, no clock, no randomness, no
floats. Input: susceptible (integer 1..12), infected (integer 1..12) and p_num / p_den,
the probability p of an infectious contact between one infective and one susceptible in
one generation (integers, p_den 1..1000, p_num 1..p_den). In each generation every
susceptible escapes infection with probability q^I, where q = 1 - p and I is the number
of infectives that generation, independently; every infective is then removed and the
newly infected become the next infectives. The chain runs until nobody is infective. It
is solved exactly over all (susceptible, infective) states, so no simulation is sampled.
The result is the exact probability of each total number of new infections 0..susceptible
(the final size distribution, summing to exactly 1), the mean final size, the probability
that nobody beyond the initial infectives is infected, the expected number of generations
with at least one infective, and the expected infectives in each generation from 0 until
the epidemic must have ended (generation susceptible + 1 at the latest). All values are
exact Fractions in strings.

Scope: PARTIAL for the Epidemic Modeling line. It solves one closed-population, one-type
Reed-Frost model with a caller-chosen contact probability. It has no births, deaths,
latent period, vaccination, heterogeneity, network structure, recovery time other than
one generation, calibration to data or forecast. (The SIR line is separate.)

Not claimed: that the model describes any real disease or population, that the contact
probability is right, that the outcome predicts anything, or anything about the real
world. Every claim flag in the result is False.
"""
from fractions import Fraction
from math import comb

MAX_S = 12
MAX_I = 12
MAX_DEN = 1000
_TOP = frozenset({"susceptible", "infected", "p_num", "p_den"})

NOT_CLAIMED = (
    "the model describes a real disease or population",
    "the contact probability is right",
    "the outcome predicts anything",
    "real-world outcome",
)
CLAIMS = {"describes_real_disease": False, "probability_right": False, "predictive": False, "real_world": False}


class EpidemicError(ValueError):
    pass


def _int(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise EpidemicError(f"{name} must be an int")
    if v < lo or v > hi:
        raise EpidemicError(f"{name} out of range")
    return v


def epidemic_chain_binomial(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise EpidemicError("data keys must be exactly susceptible, infected, p_num, p_den")
    s0 = _int(data["susceptible"], 1, MAX_S, "susceptible")
    i0 = _int(data["infected"], 1, MAX_I, "infected")
    den = _int(data["p_den"], 1, MAX_DEN, "p_den")
    num = _int(data["p_num"], 1, den, "p_num")
    q = Fraction(den - num, den)
    layer = {(s0, i0): Fraction(1)}
    final = [Fraction(0)] * (s0 + 1)
    expected_i = []
    alive = Fraction(0)
    for _ in range(s0 + 2):
        expected_i.append(sum(p * i for (s, i), p in layer.items()))
        alive += sum(p for (s, i), p in layer.items() if i > 0)
        nxt = {}
        for (s, i), p in layer.items():
            if i == 0:
                final[s0 - s] += p
                continue
            escape = q ** i
            for k in range(s + 1):
                pk = comb(s, k) * (1 - escape) ** k * escape ** (s - k)
                if pk != 0:
                    key = (s - k, k)
                    nxt[key] = nxt.get(key, Fraction(0)) + p * pk
        layer = nxt
    # s0 + 2 layers always suffice: every generation with an infective either removes at least one
    # susceptible or ends in zero infectives, so at most s0 + 1 layers hold infectives.
    return {
        "susceptible": s0,
        "infected": i0,
        "final_size_distribution": [str(x) for x in final],
        "mean_final_size": str(sum(k * x for k, x in enumerate(final))),
        "no_spread_probability": str(final[0]),
        "expected_generations": str(alive),
        "expected_infectives_by_generation": [str(x) for x in expected_i],
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }

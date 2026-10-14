import copy
import itertools

import pytest

from sugarcode.extra_doc import genetic_algorithm as m
from sugarcode.extra_doc.genetic_algorithm import GeneticError, genetic_algorithm as run

KEYS = "data keys must be exactly values, weights, capacity, population, generations, mut_num, mut_den, seed"
LITERAL_NOT_CLAIMED = [
    "the run finds the optimum",
    "the generator is statistically strong",
    "the result carries over to a real decision",
    "real-world outcome",
]
BASE = {"values": [6, 5, 4, 3], "weights": [4, 3, 2, 1], "capacity": 6, "population": 4,
        "generations": 3, "mut_num": 1, "mut_den": 8, "seed": 1}


def d(**kw):
    out = copy.deepcopy(BASE)
    out.update(kw)
    return out


def bad(data, msg):
    with pytest.raises(GeneticError) as e:
        run(data)
    assert str(e.value) == msg


def stream(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) % 2147483648
        yield x // 65536


def fit(values, weights, cap, g):
    w = sum(a for a, b in zip(weights, g) if b)
    return 0 if w > cap else sum(a for a, b in zip(values, g) if b)


def reference(cfg):
    """A second implementation written as one flat loop over a generator."""
    rnd = stream(cfg["seed"])
    n, pop = len(cfg["values"]), cfg["population"]
    P = [[next(rnd) % 2 for _ in range(n)] for _ in range(pop)]
    hist = []
    best = (-1, None)
    for gen in range(cfg["generations"] + 1):
        S = [fit(cfg["values"], cfg["weights"], cfg["capacity"], g) for g in P]
        k = S.index(max(S))
        hist.append(S[k])
        if S[k] > best[0]:
            best = (S[k], P[k][:])
        if gen == cfg["generations"]:
            break
        newP = [P[k][:]]
        while len(newP) < pop:
            picks = []
            for _ in (0, 1):
                a = next(rnd) % pop
                b = next(rnd) % pop
                picks.append(P[b] if S[b] > S[a] else P[a])
            cut = 1 + next(rnd) % (n - 1)
            kid = picks[0][:cut] + picks[1][cut:]
            for idx in range(n):
                if next(rnd) % cfg["mut_den"] < cfg["mut_num"]:
                    kid[idx] = 1 - kid[idx]
            newP.append(kid)
        P = newP
    return best, hist, P


def brute(cfg):
    n = len(cfg["values"])
    best = None
    for g in itertools.product((0, 1), repeat=n):
        f = fit(cfg["values"], cfg["weights"], cfg["capacity"], list(g))
        if best is None or f > best[0]:
            best = (f, list(g))
    return best


def test_generator_start_is_pinned_and_initial_population_by_hand():
    g = stream(1)
    assert [next(g) for _ in range(10)] == [16838, 5758, 10113, 17515, 31051, 5627, 23010, 7419, 16212, 4086]
    # first 16 outputs & 1 -> genomes 0011, 1101, 0011, 0011 ; fitness 7, 0 (weight 8 > 6), 7, 7
    out = run(d(generations=1))
    assert out["history"][0] == 7 and len(out["history"]) == 2


def test_hand_case_result():
    out = run(d())
    assert out["history"] == [7, 7, 10, 10]
    assert out["best_fitness"] == 10 and out["best_genome"] == [1, 0, 1, 0]
    assert out["optimum_fitness"] == 12 and out["optimum_genome"] == [0, 1, 1, 1]
    assert out["final_population"] == [[1, 0, 1, 0], [0, 0, 1, 1], [1, 0, 1, 0], [1, 0, 1, 0]]


def test_matches_second_implementation_over_parameter_sets():
    import random
    rng = random.Random(5)
    for _ in range(40):
        n = rng.randint(2, 9)
        cfg = {"values": [rng.randint(-5, 30) for _ in range(n)], "weights": [rng.randint(0, 12) for _ in range(n)],
               "capacity": rng.randint(0, 40), "population": rng.randint(4, 12), "generations": rng.randint(1, 12),
               "mut_den": rng.choice((1, 2, 5, 10, 100)), "seed": rng.randint(0, 2 ** 31 - 1)}
        cfg["mut_num"] = rng.randint(0, cfg["mut_den"])
        out = run(cfg)
        best, hist, final = reference(cfg)
        assert out["history"] == hist and out["best_fitness"] == best[0] and out["best_genome"] == best[1]
        assert out["final_population"] == final
        opt = brute(cfg)
        assert (out["optimum_fitness"], out["optimum_genome"]) == opt
        assert out["best_fitness"] <= out["optimum_fitness"]


def test_elitism_makes_history_non_decreasing_and_best_matches_max():
    cfg = d(generations=30, population=20, seed=12345, mut_num=1, mut_den=10)
    out = run(cfg)
    assert out["history"] == sorted(out["history"]) and len(out["history"]) == 31
    assert out["best_fitness"] == max(out["history"])
    assert fit(cfg["values"], cfg["weights"], cfg["capacity"], out["best_genome"]) == out["best_fitness"]


def test_determinism_and_seed_sensitivity():
    assert run(d(seed=7)) == run(d(seed=7))
    finals = {str(run(d(seed=s, generations=5))["final_population"]) for s in range(8)}
    assert len(finals) > 1


def test_infeasible_everything_scores_zero_and_ties_pick_first():
    out = run(d(capacity=0, weights=[1, 1, 1, 1]))
    assert out["optimum_fitness"] == 0 and out["optimum_genome"] == [0, 0, 0, 0]
    assert out["best_fitness"] == 0
    out = run(d(values=[0, 0, 0, 0]))
    assert out["optimum_genome"] == [0, 0, 0, 0] and out["best_fitness"] == 0
    # negative values: the empty selection (fitness 0) beats any positive-weight negative total
    out = run(d(values=[-3, -2, -1, -4], weights=[0, 0, 0, 0], capacity=5))
    assert out["optimum_fitness"] == 0 and out["optimum_genome"] == [0, 0, 0, 0]


def test_full_mutation_and_no_mutation_extremes():
    r = reference(d(mut_num=8, mut_den=8))
    assert run(d(mut_num=8, mut_den=8))["final_population"] == r[2]
    r = reference(d(mut_num=0))
    assert run(d(mut_num=0))["final_population"] == r[2]


def test_claims_and_input_not_mutated():
    data = d()
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"finds_optimum": False, "generator_strong": False, "real_decision": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    out["final_population"][0][0] = 9
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert again["final_population"][0][0] != 9
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MIN_N, m.MAX_N, m.MAX_VALUE, m.MAX_CAP, m.MIN_POP, m.MAX_POP, m.MAX_GEN, m.MAX_DEN, m.MAX_SEED) == \
        (2, 16, 1000, 16000, 4, 20, 30, 1000, 2147483647)


def test_refusals_and_caps():
    for x in (None, [], {"values": []}, dict(d(), extra=1)):
        bad(x, KEYS)
    bad(d(values="ab"), "values must be a list")
    bad(d(weights=(1, 2)), "weights must be a list")
    bad(d(values=[1]), "values length out of range")
    bad(d(values=[1] * 17, weights=[1] * 17), "values length out of range")
    bad(d(weights=[1]), "weights length out of range")
    bad(d(weights=[1] * 17), "weights length out of range")
    bad(d(weights=[1, 2, 3]), "values and weights must have the same length")
    run(d(values=[1] * 16, weights=[1] * 16, generations=1))
    for name in ("capacity", "population", "generations", "mut_num", "mut_den", "seed"):
        for v in (True, 1.0, "1", None):
            bad(d(**{name: v}), f"{name} must be an int")
    bad(d(capacity=-1), "capacity out of range")
    bad(d(capacity=16001), "capacity out of range")
    run(d(capacity=16000))
    run(d(capacity=0))
    bad(d(population=3), "population out of range")
    bad(d(population=21), "population out of range")
    run(d(population=20))
    bad(d(generations=0), "generations out of range")
    bad(d(generations=31), "generations out of range")
    run(d(generations=30))
    bad(d(mut_den=0), "mut_den out of range")
    bad(d(mut_den=1001), "mut_den out of range")
    bad(d(mut_num=-1), "mut_num out of range")
    bad(d(mut_num=9), "mut_num out of range")
    run(d(mut_den=1000, mut_num=1000))
    bad(d(seed=-1), "seed out of range")
    bad(d(seed=2147483648), "seed out of range")
    run(d(seed=2147483647))
    run(d(seed=0))
    for v in (True, 1.0, "1", None):
        bad(d(values=[v, 1, 1, 1]), "value must be an int")
        bad(d(weights=[v, 1, 1, 1]), "weight must be an int")
    bad(d(values=[1001, 1, 1, 1]), "value out of range")
    bad(d(values=[-1001, 1, 1, 1]), "value out of range")
    bad(d(weights=[-1, 1, 1, 1]), "weight out of range")
    bad(d(weights=[1001, 1, 1, 1]), "weight out of range")
    run(d(values=[1000, -1000, 1, 1], weights=[1000, 0, 1, 1]))

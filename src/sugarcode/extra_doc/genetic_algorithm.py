"""Genetic Algorithms - exact deterministic evolution of 0/1 knapsack solutions.

Pure function over caller data. No retrieval, no network, no clock, no floats and no
hidden randomness: all choices come from a fixed integer generator seeded by the caller.
Input: values and weights (2..16 integers each, values -1000..1000, weights 0..1000),
capacity (integer 0..16000), population (integer 4..20), generations (integer 1..30),
mut_num / mut_den (per-gene flip probability, mut_den 1..1000, mut_num 0..mut_den) and
seed (integer 0..2147483647). A genome is a 0/1 list; its fitness is the sum of the chosen
values when the chosen weights fit within capacity and 0 otherwise.
Generator: x -> (1103515245 * x + 12345) mod 2^31, output (x >> 16) after each step.
Procedure: the initial population draws each gene as output & 1, individual by
individual. Each generation keeps the first best individual, then fills the rest with
children: two tournament selections (draw i and j as output mod population, the higher
fitness wins, the first drawn on a tie), one-point crossover at 1 + output mod (length - 1),
then each gene flips when output mod mut_den < mut_num. The result gives the best genome
and fitness found, the best fitness of every generation (the initial population is
generation 0), the final population, and the exact optimum by exhaustive search over all
2^length genomes with the optimum genome (the first in binary counting order), so a
caller can see how far the run is from it.

Scope: PARTIAL for the Genetic Algorithms line. It is one fixed algorithm on one problem
type with a fixed generator; no other encodings, operators, constraints handling beyond a
zero penalty, no adaptive rates, no parallel islands, no convergence guarantee.

Not claimed: that the run finds the optimum, that the generator is statistically strong,
that the result carries over to any real decision, or anything about the real world.
Every claim flag in the result is False.
"""
MIN_N = 2
MAX_N = 16
MAX_VALUE = 1000
MAX_CAP = 16000
MIN_POP = 4
MAX_POP = 20
MAX_GEN = 30
MAX_DEN = 1000
MAX_SEED = 2147483647
_TOP = frozenset({"values", "weights", "capacity", "population", "generations", "mut_num", "mut_den", "seed"})
_A, _C, _M = 1103515245, 12345, 2 ** 31

NOT_CLAIMED = (
    "the run finds the optimum",
    "the generator is statistically strong",
    "the result carries over to a real decision",
    "real-world outcome",
)
CLAIMS = {"finds_optimum": False, "generator_strong": False, "real_decision": False, "real_world": False}


class GeneticError(ValueError):
    pass


def _int(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise GeneticError(f"{name} must be an int")
    if v < lo or v > hi:
        raise GeneticError(f"{name} out of range")
    return v


def _list(v, name):
    if not isinstance(v, list):
        raise GeneticError(f"{name} must be a list")
    if not MIN_N <= len(v) <= MAX_N:
        raise GeneticError(f"{name} length out of range")
    return v


class _Rng:
    def __init__(self, seed):
        self.x = seed

    def next(self):
        self.x = (_A * self.x + _C) % _M
        return self.x >> 16


def genetic_algorithm(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise GeneticError("data keys must be exactly values, weights, capacity, population, generations, mut_num, mut_den, seed")
    values_in = _list(data["values"], "values")
    weights_in = _list(data["weights"], "weights")
    if len(values_in) != len(weights_in):
        raise GeneticError("values and weights must have the same length")
    cap = _int(data["capacity"], 0, MAX_CAP, "capacity")
    pop = _int(data["population"], MIN_POP, MAX_POP, "population")
    gens = _int(data["generations"], 1, MAX_GEN, "generations")
    den = _int(data["mut_den"], 1, MAX_DEN, "mut_den")
    num = _int(data["mut_num"], 0, den, "mut_num")
    seed = _int(data["seed"], 0, MAX_SEED, "seed")
    values = [_int(v, -MAX_VALUE, MAX_VALUE, "value") for v in values_in]
    weights = [_int(w, 0, MAX_VALUE, "weight") for w in weights_in]
    n = len(values)

    def fitness(g):
        if sum(w for w, b in zip(weights, g) if b) > cap:
            return 0
        return sum(v for v, b in zip(values, g) if b)

    rng = _Rng(seed)
    population = [[rng.next() & 1 for _ in range(n)] for _ in range(pop)]
    history = []
    best = None
    for gen in range(gens + 1):
        scores = [fitness(g) for g in population]
        top = max(range(pop), key=lambda i: (scores[i], -i))
        history.append(scores[top])
        if best is None or scores[top] > best[0]:
            best = (scores[top], list(population[top]))
        if gen == gens:
            break
        nxt = [list(population[top])]
        while len(nxt) < pop:
            parents = []
            for _ in range(2):
                i, j = rng.next() % pop, rng.next() % pop
                parents.append(population[j] if scores[j] > scores[i] else population[i])
            cp = 1 + rng.next() % (n - 1)
            child = parents[0][:cp] + parents[1][cp:]
            child = [b ^ 1 if rng.next() % den < num else b for b in child]
            nxt.append(child)
        population = nxt
    opt = None
    for mask in range(2 ** n):
        g = [(mask >> (n - 1 - k)) & 1 for k in range(n)]
        f = fitness(g)
        if opt is None or f > opt[0]:
            opt = (f, g)
    return {
        "best_fitness": best[0],
        "best_genome": best[1],
        "history": history,
        "final_population": [list(g) for g in population],
        "optimum_fitness": opt[0],
        "optimum_genome": opt[1],
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }

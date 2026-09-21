from __future__ import annotations
import random


def evolve(pathway_genes: list[str] | None = None, generations: int = 2000,
           pop_size: int = 500, mutation_rate: float = 1e-3, burden_cost: float = 0.08,
           selection_on_yield: float = 0.5, seed: int = 42,
           sample_every: int = 100) -> dict:
    """Multi-generation evolutionary simulation of an engineered pathway.

    Each individual carries expression levels per pathway gene. Fitness =
    growth (1 - burden) + yield advantage. Mutations tune expression up/down
    or knock genes out (loss-of-function). Tracks dominant genotype and the
    classic failure mode: silencing of the burdensome pathway.
    """
    genes = pathway_genes or ["enzymeA", "enzymeB", "transporter"]
    rng = random.Random(seed)
    # population: list of expression dicts; founder expresses all at 1.0
    pop = [{g: 1.0 for g in genes} for _ in range(pop_size)]

    def fitness(ind):
        expr = sum(ind[g] for g in genes)
        burden = burden_cost * expr
        yld = selection_on_yield * min(expr / len(genes), 1.5)
        return max(0.01, 1.0 - burden + yld)

    history, snapshots = [], []
    dominant_gen = None
    for gen in range(1, generations + 1):
        fits = [fitness(ind) for ind in pop]
        total = sum(fits)
        # fitness-proportional reproduction
        new_pop = []
        cum, c = [], 0.0
        for f in fits:
            c += f / total
            cum.append(c)
        for _ in range(pop_size):
            r = rng.random()
            for i, cp in enumerate(cum):
                if r <= cp:
                    child = dict(pop[i])
                    break
            # mutation
            if rng.random() < mutation_rate * len(genes):
                g = rng.choice(genes)
                roll = rng.random()
                if roll < 0.15:
                    child[g] = 0.0                      # loss of function
                elif roll < 0.6:
                    child[g] = max(0.0, child[g] - rng.random() * 0.3)
                else:
                    child[g] = child[g] + rng.random() * 0.3
            new_pop.append(child)
        pop = new_pop
        if gen % sample_every == 0:
            mean_expr = {g: round(sum(i[g] for i in pop) / pop_size, 3) for g in genes}
            frac_ko = round(sum(1 for i in pop if any(i[g] == 0.0 for g in genes)) / pop_size, 3)
            mean_fit = round(sum(fitness(i) for i in pop) / pop_size, 4)
            history.append({"gen": gen, "mean_expression": mean_expr,
                            "knockout_fraction": frac_ko, "mean_fitness": mean_fit})
            if frac_ko > 0.5 and dominant_gen is None:
                dominant_gen = gen
    final = history[-1]
    silenced = final["knockout_fraction"] > 0.5
    return {
        "genes": genes, "generations": generations,
        "history": history,
        "dominant_genotype": final["mean_expression"],
        "pathway_silenced": silenced,
        "silencing_onset_gen": dominant_gen,
        "predicted_adaptations": _adaptations(final, silenced),
        "design_recommendations": _recommend(silenced, burden_cost),
    }


def _adaptations(final, silenced):
    if silenced:
        return ["loss-of-function sweeps the population - cells escape pathway burden",
                "expression of remaining copies tunes downward"]
    return ["expression re-tunes toward burden-yield optimum",
            "no knockout fixation observed - construct genetically stable"]


def _recommend(silenced, burden):
    rec = ["integrate pathway into essential-gene locus to couple escape to fitness cost",
           "add addiction module (toxin-antitoxin) to plasmid"]
    if silenced or burden > 0.05:
        rec.append("reduce expression strength or split pathway across co-culture members")
    return rec

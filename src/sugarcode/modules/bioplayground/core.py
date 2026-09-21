from __future__ import annotations
import random


def run_sandbox(pop_size: int = 200, generations: int = 300, n_alleles: int = 3,
                fitness: list[float] | None = None, mutation_rate: float = 1e-4,
                bottleneck_at: int | None = None, bottleneck_size: int = 20,
                seed: int = 42) -> dict:
    """Wright-Fisher drift + selection + mutation on a multi-allele construct locus.

    fitness: per-allele selection coefficients (allele 0 = engineered construct).
    Bottleneck events model environmental shocks (e.g. antibiotic pulse).
    """
    if pop_size < bottleneck_size:
        raise ValueError("population must exceed bottleneck size")
    rng = random.Random(seed)
    n = n_alleles
    fit = fitness or [1.0] + [0.98] * (n - 1)
    if len(fit) != n:
        raise ValueError("fitness must match n_alleles")
    freq = [1.0] + [0.0] * (n - 1)
    trajectory = [list(freq)]
    fixed_at = None
    events = []
    for gen in range(1, generations + 1):
        # selection
        w_bar = sum(f * w for f, w in zip(freq, fit))
        sel = [f * w / w_bar for f, w in zip(freq, fit)]
        # symmetric mutation
        mut = [s * (1 - mutation_rate) + mutation_rate * (1 - s) / (n - 1) if n > 1 else s
               for s in sel]
        # drift: multinomial sampling
        size = bottleneck_size if gen == bottleneck_at else pop_size
        if gen == bottleneck_at:
            events.append({"gen": gen, "event": "bottleneck", "size": size})
        draws = [rng.random() for _ in range(size)]
        cum, counts = [], [0] * n
        c = 0.0
        for i, m in enumerate(mut):
            c += m
            cum.append(c)
        for d in draws:
            for i, cp in enumerate(cum):
                if d <= cp:
                    counts[i] += 1
                    break
        freq = [c / size for c in counts]
        if gen % 10 == 0:
            trajectory.append([round(f, 4) for f in freq])
        if freq[0] == 0.0 and fixed_at is None:
            fixed_at = gen
            events.append({"gen": gen, "event": "construct_lost"})
            break
        if freq[0] >= 0.999 and fixed_at is None:
            fixed_at = gen
            events.append({"gen": gen, "event": "construct_fixed"})
            break
    return {
        "pop_size": pop_size, "generations_run": len(trajectory) * 10,
        "final_construct_freq": round(freq[0], 4),
        "construct_retained": freq[0] > 0.5,
        "fixation_gen": fixed_at,
        "events": events,
        "trajectory_every_10gen": trajectory,
        "interpretation": _interpret(freq[0], fixed_at, fit),
    }


def _interpret(f0, fixed_at, fit):
    if f0 > 0.5:
        return ("engineered allele stable - selection coefficient "
                f"{fit[0]:.3f} holds it against drift")
    return (f"engineered allele lost by gen {fixed_at} - fitness cost of the construct "
            "exceeds what drift can tolerate; consider burden reduction or selection marker")

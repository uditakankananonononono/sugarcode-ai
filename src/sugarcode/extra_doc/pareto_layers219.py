"""Exact finite-menu Pareto fronts and domination witnesses.
NOT_CLAIMED: global continuous Pareto frontier; authentic feasibility; preferred
tradeoff choice; real-world execution; runtime integration.
"""
from fractions import Fraction
import math

def identify(options, directions):
    if type(directions) is not list or not 1 <= len(directions) <= 8:
        raise ValueError('1..8 Pareto directions before scan')
    if any((type(v) is not str or v not in ('min', 'max') for v in directions)):
        raise ValueError('Pareto direction min or max')
    if type(options) is not list or not 1 <= len(options) <= 100:
        raise ValueError('1..100 Pareto options before scan')
    d = len(directions)
    ids = []
    values = []
    for row in options:
        if type(row) is not dict or set(row) != {'id', 'values'}:
            raise ValueError('exact Pareto id/values fields')
        ident = row['id']
        raw = row['values']
        if type(ident) is not str or not 1 <= len(ident) <= 120 or (not ident.strip()) or (ident in ids):
            raise ValueError('unique nonblank Pareto ids 1..120')
        if type(raw) is not list or len(raw) != d:
            raise ValueError('one Pareto value per direction')
        vec = []
        for v, way in zip(raw, directions):
            if type(v) not in (int, float) or not -1000000 <= v <= 1000000 or (not math.isfinite(v)):
                raise ValueError('strict finite Pareto value within -1000000..1000000')
            vec.append(Fraction(str(v)) if way == 'min' else -Fraction(str(v)))
        ids.append(ident)
        values.append(vec)

    def dominates(a, b):
        return all((x <= y for x, y in zip(a, b))) and any((x < y for x, y in zip(a, b)))
    witnesses = {ids[j]: sorted((ids[i] for i in range(len(ids)) if dominates(values[i], values[j]))) for j in range(len(ids))}
    remaining = set(range(len(ids)))
    layers = []
    ranks = {}
    while remaining:
        front = [j for j in remaining if not any((dominates(values[i], values[j]) for i in remaining))]
        labels = sorted((ids[j] for j in front))
        layers.append(labels)
        for j in front:
            ranks[ids[j]] = len(layers) - 1
        remaining -= set(front)
    return {'frontier_ids': layers[0], 'layers': layers, 'rank': {k: ranks[k] for k in sorted(ranks)}, 'dominating_ids': witnesses, 'directions': directions[:], 'definition': 'weakly no worse on every objective and strictly better on at least one; equal vectors do not dominate', 'frontier_scope': 'only supplied feasible option menu', 'global_frontier_verified': False, 'external_effects': []}

"""Exact finite-scenario integer inventory plan with shortage/excess recourse.
NOT_CLAIMED: authentic demand distribution; general stochastic optimizer;
real purchase; runtime integration; expected performance outside supplied model.
"""
from fractions import Fraction
import math

def plan(quantities, scenarios, purchase, shortage, holding):

    def number(v):
        if type(v) not in (int, float) or not 0 <= v <= 1000000 or (not math.isfinite(v)):
            raise ValueError('strict finite nonnegative cost within 1000000')
        return Fraction(str(v))
    costs = [number(v) for v in (purchase, shortage, holding)]
    if type(quantities) is not list or not 1 <= len(quantities) <= 100:
        raise ValueError('1..100 candidate quantities before scan')
    if any((type(q) is not int or not 0 <= q <= 10000 for q in quantities)):
        raise ValueError('strict quantity integers within 0..10000')
    if len(set(quantities)) != len(quantities):
        raise ValueError('unique quantity choices')
    if type(scenarios) is not list or not 1 <= len(scenarios) <= 100:
        raise ValueError('1..100 demand scenarios before scan')
    rows = []
    ids = set()
    for s in scenarios:
        if type(s) is not dict or set(s) != {'id', 'demand', 'probability'}:
            raise ValueError('exact id/demand/probability fields')
        if type(s['id']) is not str or not 1 <= len(s['id']) <= 120 or s['id'] in ids:
            raise ValueError('unique nonempty scenario id up to 120 characters')
        ids.add(s['id'])
        d = s['demand']
        p = s['probability']
        if type(d) is not int or not 0 <= d <= 10000:
            raise ValueError('strict demand integers within 0..10000')
        if type(p) not in (int, float) or not 0 <= p <= 1 or (not math.isfinite(p)):
            raise ValueError('strict finite probability within 0..1')
        rows.append((s['id'], d, Fraction(str(p))))
    if sum((p for _, _, p in rows)) != 1:
        raise ValueError('scenario probabilities must sum exactly to one')
    choices = []
    perfect = []
    for q in sorted(quantities):
        outcomes = []
        expected = Fraction(0)
        for name, d, p in rows:
            missing = max(d - q, 0)
            left = max(q - d, 0)
            total = costs[0] * q + costs[1] * missing + costs[2] * left
            expected += p * total
            outcomes.append({'id': name, 'shortage': missing, 'excess': left, 'cost_fraction': str(total)})
        choices.append({'quantity': q, 'expected_cost_fraction': str(expected), 'scenario_outcomes': outcomes})
    selected = min(choices, key=lambda c: (Fraction(c['expected_cost_fraction']), c['quantity']))
    for j, (name, d, p) in enumerate(rows):
        oracle = min(choices, key=lambda c: (Fraction(c['scenario_outcomes'][j]['cost_fraction']), c['quantity']))
        perfect.append(p * Fraction(oracle['scenario_outcomes'][j]['cost_fraction']))
    oracle_cost = sum(perfect)
    best = Fraction(selected['expected_cost_fraction'])
    return {'selected_quantity': selected['quantity'], 'expected_cost_fraction': str(best), 'choices': choices, 'perfect_information_expected_cost_fraction': str(oracle_cost), 'expected_value_of_perfect_information_fraction': str(best - oracle_cost), 'optimality_scope': 'only supplied finite quantity menu and demand distribution', 'recourse': 'nonnegative shortage and excess after demand observation', 'probabilities_verified': False, 'purchase_executed': False, 'external_effects': []}

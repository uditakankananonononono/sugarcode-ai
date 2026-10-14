"""Row 490 Scenario Planning: exact option-by-scenario payoff analysis.

The caller supplies 1 to 6 unique scenarios (name, weight), weight an int 0 to 1000 with a positive
total (relative likelihoods chosen by the caller), 1 to 6 unique options (name, payoffs) with one
int payoff from -10**6 to 10**6 per scenario. Reported, all exact: scenario probabilities
(weight / total, Fractions); per option the expected payoff, the worst payoff and the largest
regret (best payoff in a scenario minus the option's payoff, maximised over scenarios); and the
option with the best expected payoff, the best worst case (maximin) and the smallest largest
regret (minimax regret), each first listed on ties. Caps are implementation choices, not spec
values. Nothing is forecast; the numbers are the caller's.
NOT_CLAIMED: that the scenarios are plausible or complete, that the weights or payoffs are
measured or right, that any option should be chosen or that a decision rule is appropriate,
forecasts, financial, legal or approval-gate clearance, deployment.
"""
from fractions import Fraction

NOT_CLAIMED = ('scenarios plausible or complete', 'weights or payoffs measured or right',
               'any option should be chosen or a decision rule is appropriate', 'any forecast',
               'financial, legal or approval-gate clearance', 'deployment')


def _name(v):
    if type(v) is not str:
        raise TypeError('names must be str')
    if not 1 <= len(v) <= 40:
        raise ValueError('names must be 1 to 40 characters')


def analyse_scenarios(scenarios, options):
    if type(scenarios) not in (list, tuple) or type(options) not in (list, tuple):
        raise TypeError('scenarios and options must be a list or tuple')
    if not 1 <= len(scenarios) <= 6:
        raise ValueError('scenario count must be between 1 and 6')
    if not 1 <= len(options) <= 6:
        raise ValueError('option count must be between 1 and 6')
    sc = []
    for s in scenarios:
        if type(s) not in (list, tuple) or len(s) != 2:
            raise ValueError('each scenario must be (name, weight)')
        _name(s[0])
        if type(s[1]) is not int:
            raise TypeError('weights must be nonbool int')
        if not 0 <= s[1] <= 1000:
            raise ValueError('weights must be between 0 and 1000')
        sc.append((s[0], s[1]))
    if len({s[0] for s in sc}) != len(sc):
        raise ValueError('scenario names must be unique')
    total = sum(s[1] for s in sc)
    if total <= 0:
        raise ValueError('weights must have a positive total')
    ops = []
    for o in options:
        if type(o) not in (list, tuple) or len(o) != 2:
            raise ValueError('each option must be (name, payoffs)')
        _name(o[0])
        pay = o[1]
        if type(pay) not in (list, tuple) or len(pay) != len(sc):
            raise ValueError('each option needs one payoff per scenario')
        for p in pay:
            if type(p) is not int:
                raise TypeError('payoffs must be nonbool int')
            if not -10 ** 6 <= p <= 10 ** 6:
                raise ValueError('payoffs must be between -1000000 and 1000000')
        ops.append((o[0], tuple(pay)))
    if len({o[0] for o in ops}) != len(ops):
        raise ValueError('option names must be unique')
    probs = [Fraction(s[1], total) for s in sc]
    best = [max(o[1][j] for o in ops) for j in range(len(sc))]
    out = [{'name': n, 'expected': sum(p * x for p, x in zip(probs, pay)), 'worst': min(pay),
            'max_regret': max(best[j] - pay[j] for j in range(len(sc)))} for n, pay in ops]
    pick = lambda key: out[min(range(len(out)), key=lambda i: (key(out[i]), i))]['name']
    return {'probabilities': probs, 'options': out,
            'best_expected': pick(lambda o: -o['expected']), 'maximin': pick(lambda o: -o['worst']),
            'minimax_regret': pick(lambda o: o['max_regret']),
            'scenarios_validated': False, 'not_claimed': NOT_CLAIMED}

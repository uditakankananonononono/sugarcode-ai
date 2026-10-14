"""Row 355 Speculative Design: finite enumeration of internally consistent futures (exact).

A scenario picks one value on every axis (for example axis 'energy', value 'scarce').
The caller supplies pairs of (axis, value) choices that cannot co-occur. All
scenarios that contain no forbidden pair are listed in axis-then-value input order,
with how many consistent scenarios use each value. 1 to 4 axes, 1 to 4 values per
axis (at most 256 scenarios), at most 16 forbidden pairs; names and values are 1 to
40 character strings; axis names and the values inside an axis are unique.
Caps are implementation choices, not spec values. Nothing here is a forecast.
NOT_CLAIMED: probability, likelihood or plausibility of any scenario, forecasting,
that the axes or forbidden pairs are complete or correct, desirability, social or
ethical assessment, user research, design quality, deployment.
"""
from itertools import product

NOT_CLAIMED = ('probability or likelihood', 'plausibility', 'forecasting',
               'axes and constraints are complete or correct', 'desirability', 'social or ethical assessment',
               'user research', 'design quality', 'deployment')


def _name(v):
    if type(v) is not str:
        raise TypeError('names and values must be str')
    if not 1 <= len(v) <= 40:
        raise ValueError('names and values must be 1 to 40 characters')
    return v


def explore_futures(axes, forbidden_pairs=()):
    if type(axes) not in (list, tuple):
        raise TypeError('axes must be a list or tuple')
    if not 1 <= len(axes) <= 4:
        raise ValueError('axis count must be between 1 and 4')
    parsed = []
    for axis in axes:
        if type(axis) not in (list, tuple) or len(axis) != 2:
            raise ValueError('each axis must be (name, values)')
        if type(axis[1]) not in (list, tuple) or not 1 <= len(axis[1]) <= 4:
            raise ValueError('each axis must have between 1 and 4 values')
        parsed.append((_name(axis[0]), tuple(_name(v) for v in axis[1])))
    if len({a[0] for a in parsed}) != len(parsed):
        raise ValueError('axis names must be unique')
    if any(len(set(a[1])) != len(a[1]) for a in parsed):
        raise ValueError('values within an axis must be unique')
    if type(forbidden_pairs) not in (list, tuple):
        raise TypeError('forbidden_pairs must be a list or tuple')
    if len(forbidden_pairs) > 16:
        raise ValueError('at most 16 forbidden pairs')
    domain = {a[0]: set(a[1]) for a in parsed}
    pairs = []
    for pair in forbidden_pairs:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise ValueError('each forbidden pair must contain two (axis, value) choices')
        choices = []
        for choice in pair:
            if type(choice) not in (list, tuple) or len(choice) != 2:
                raise ValueError('each choice must be (axis, value)')
            choices.append((_name(choice[0]), _name(choice[1])))
        if any(ax not in domain or val not in domain[ax] for ax, val in choices):
            raise ValueError('forbidden pairs may only use listed axes and values')
        if choices[0][0] == choices[1][0]:
            raise ValueError('a forbidden pair must name two different axes')
        pairs.append(frozenset(choices))
    scenarios = []
    for combo in product(*(a[1] for a in parsed)):
        chosen = frozenset((parsed[k][0], v) for k, v in enumerate(combo))
        if any(p <= chosen for p in pairs):
            continue
        scenarios.append({parsed[k][0]: v for k, v in enumerate(combo)})
    usage = {a[0]: {v: sum(1 for s in scenarios if s[a[0]] == v) for v in a[1]} for a in parsed}
    total = 1
    for a in parsed:
        total *= len(a[1])
    return {'scenarios': scenarios, 'consistent_count': len(scenarios), 'candidate_count': total,
            'excluded_count': total - len(scenarios), 'value_usage': usage,
            'forecast_validated': False, 'not_claimed': NOT_CLAIMED}

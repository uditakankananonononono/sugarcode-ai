"""Row 547: A/B Testing Infrastructure - Enables experiments.

Bounded planning aid over caller supplied rows. No external actions, persistence,
capability development evidence, organization quality, or optimal policy claim.
Explicit import only; 1..32 tuple rows. Labels are lowercase ASCII identifiers.
"""
import re

LABEL = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if len(value) > 24 or LABEL.fullmatch(value) is None:
        raise ValueError('label must be 1..24 lowercase identifier characters')


def _integer(value, low, high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low <= value <= high:
        raise ValueError('integer outside declared range')


def _rows(rows, arity):
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1 <= len(rows) <= 32:
        raise ValueError('row count must be 1..32')
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row) != arity:
            raise ValueError('wrong row arity')


def summarize_experiment(rows):
    """Rows: (unit_id, assigned_arm 0/1, converted_bit 0/1).
    Summarize supplied randomization/outcome declarations as exact conversion
    rates and treatment-minus-control difference. No actual assignment service,
    exposure tracking, significance, causal claim or experiment deployment.
    """
    _rows(rows, 3)
    for unit, arm, converted in rows:
        _label(unit)
        _integer(arm, 0, 1)
        _integer(converted, 0, 1)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate unit')
    if {x[1] for x in rows} != {0,1}:
        raise ValueError('both experiment arms required')
    from fractions import Fraction as F
    arms = []
    rates = []
    for arm in (0,1):
        outcomes = [converted for _,group,converted in rows if group==arm]
        rate = F(sum(outcomes),len(outcomes))
        rates.append(rate)
        arms.append((arm,len(outcomes),sum(outcomes),str(rate)))
    return {'arms': arms, 'difference_fraction': str(rates[1]-rates[0])}

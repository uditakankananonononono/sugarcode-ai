"""Row 757: War Gaming - Simulates conflict.

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


def simulate_business_capacity_scenarios(rows):
    """Rows: (scenario_id, base_demand, declared_demand_shock, capacity).
    Abstract business demand/capacity stress arithmetic only, no military,
    conflict tactics, adversary strategy or actual war gaming. Report shortfall
    and utilization fraction, None at zero capacity. No forecasting guarantee.
    """
    _rows(rows, 4)
    for scenario,demand,shock,capacity in rows:
        _label(scenario)
        _integer(demand, 0, 1000000)
        _integer(shock, 0, 1000000)
        _integer(capacity, 0, 1000000)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate scenario')
    from fractions import Fraction as F
    scenarios=[]
    for scenario,demand,shock,capacity in sorted(rows):
        total=demand+shock
        scenarios.append((scenario,total,max(0,total-capacity),str(F(total,capacity)) if capacity else None))
    return {'scenarios':scenarios,'shortfall_count':sum(x[2]>0 for x in scenarios)}

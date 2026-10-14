"""Row 641, Capacity Planning: exact compound demand growth against a fixed capacity.

Demand starts at current and is multiplied by (100 + growth_percent) / 100 each
period, using exact Fractions. Reported per period 1 to periods: demand rounded
up to a whole unit, headroom (capacity minus that rounded demand, negative when
over) and first_breach_period: 0 if current demand already exceeds capacity,
else the first period whose exact demand exceeds capacity, else None.
Caps (checked before any work): current 1 to 1000000, growth_percent 0 to 100,
periods 1 to 24, capacity 1 to 1000000000, all nonbool ints.
NOT_CLAIMED: forecasting accuracy, seasonality, non-compound growth, cost,
autoscaling behavior, production readiness.
"""
from fractions import Fraction

SCOPE = 'PARTIAL: exact compound growth arithmetic against one fixed capacity'
NOT_CLAIMED = ('forecasting accuracy', 'seasonality', 'non-compound growth', 'cost',
               'autoscaling behavior', 'production readiness')


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def capacity_plan(current, growth_percent, periods, capacity):
    _int(current, 1, 1000000, 'current must be a nonbool integer between 1 and 1000000')
    _int(growth_percent, 0, 100, 'growth_percent must be a nonbool integer between 0 and 100')
    _int(periods, 1, 24, 'periods must be a nonbool integer between 1 and 24')
    _int(capacity, 1, 1000000000, 'capacity must be a nonbool integer between 1 and 1000000000')
    factor = Fraction(100 + growth_percent, 100)
    demand = Fraction(current)
    first = 0 if demand > capacity else None
    rounded = []
    for t in range(1, periods + 1):
        demand *= factor
        rounded.append(-((-demand.numerator) // demand.denominator))
        if first is None and demand > capacity:
            first = t
    return {'demand': rounded, 'headroom': [capacity - d for d in rounded], 'first_breach_period': first}

"""Row 759: Simulation - Models scenarios.

SCOPED planning aid over caller supplied rows. No external actions, persistence,
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


def simulate_inventory_steps(rows):
    """Rows: (step_id, arrivals, demand), in time-step order. Inventory
    starts0, arrivals precede demand, unmet demand lost (not backlogged).
    Fixed finite inventory model, no world model/general simulation/forecasting
    or external execution. Return per-step served/lost/remaining and totals.
    """
    _rows(rows, 3)
    for step,arrivals,demand in rows:
        _label(step)
        _integer(arrivals, 0, 1000000)
        _integer(demand, 0, 1000000)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate step')
    stock=0
    trace=[]
    for step,arrivals,demand in rows:
        stock+=arrivals
        served=min(stock,demand)
        lost=demand-served
        stock-=served
        trace.append((step,served,lost,stock))
    return {'steps':trace,'served':sum(x[1] for x in trace),'lost':sum(x[2] for x in trace),'remaining':stock}

"""Row 623: Blue-Green Deployment - Enables zero-downtime.

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


def plan_switches(rows):
    """Rows: (scenario_id, initial_color_bit, blue_healthy_bit,
    green_healthy_bit), color0=blue,1=green. Switch to other color only when
    destination declared healthy. Report prior/final route and declared final
    health. No deployment executed; zero downtime NOT demonstrated/guaranteed.
    """
    _rows(rows, 4)
    for scenario,current,blue,green in rows:
        _label(scenario)
        _integer(current, 0, 1)
        _integer(blue, 0, 1)
        _integer(green, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate scenario')
    outcomes=[]
    for scenario,current,blue,green in sorted(rows):
        destination=1-current
        health=(blue,green)
        switched=health[destination]==1
        final=destination if switched else current
        outcomes.append((scenario,current,final,switched,bool(health[final])))
    return {'switches':outcomes,'blocked_count':sum(not x[3] for x in outcomes)}

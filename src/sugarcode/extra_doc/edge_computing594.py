"""Row 594: Edge Computing - Processes near source.

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


def choose_placement(rows):
    """Rows: (task_id, supplied_edge_latency, cloud_latency, local_only_bit).
    Choose edge for local-only tasks or edge<=cloud latency; otherwise cloud.
    Pure placement planning, no source proximity measurement or deployment.
    """
    _rows(rows, 4)
    for task, edge, cloud, local_only in rows:
        _label(task)
        _integer(edge, 0, 1000000)
        _integer(cloud, 0, 1000000)
        _integer(local_only, 0, 1)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate task')
    plan = [(task,'edge' if local_only==1 or edge<=cloud else 'cloud',
             edge if local_only==1 or edge<=cloud else cloud)
            for task,edge,cloud,local_only in sorted(rows)]
    return {'placements':plan,'total_latency':sum(x[2] for x in plan)}

"""Row 609: Chaos Engineering - Tests resilience.

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


def simulate_failover(rows):
    """Rows: (scenario_id, primary_failed_bit, backup_failed_bit,
    failover_enabled_bit). Exercise fixed primary/backup resilience logic.
    Return route or unavailable. No faults injected into real services, no
    actual recovery/availability/resilience claim. Independent scenarios only.
    """
    _rows(rows, 4)
    for scenario, primary_failed, backup_failed, failover in rows:
        _label(scenario)
        _integer(primary_failed, 0, 1)
        _integer(backup_failed, 0, 1)
        _integer(failover, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate scenario')
    outcomes=[]
    for scenario,primary_failed,backup_failed,failover in sorted(rows):
        if primary_failed==0:
            route='primary'
        elif failover==1 and backup_failed==0:
            route='backup'
        else:
            route='unavailable'
        outcomes.append((scenario,route))
    return {'outcomes':outcomes,'unavailable':sum(route=='unavailable' for _,route in outcomes)}

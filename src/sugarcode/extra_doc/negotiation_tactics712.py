"""Row 712: Negotiation Tactics - Achieves favorable outcomes.

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


def compare_supplied_offers(rows):
    """Rows: (offer_id, offered_value, declared_reservation_floor,
    concession_cost). Among offers meeting floor, maximize value minus cost,
    tie ID. Pure finite suppliedoffer rubric, no bargaining/contact/acceptance,
    actual favorable outcome, utility measurement or binding negotiation.
    """
    _rows(rows, 4)
    for offer,value,floor,cost in rows:
        _label(offer)
        _integer(value, 0, 1000000)
        _integer(floor, 0, 1000000)
        _integer(cost, 0, 1000000)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate offer')
    eligible=[(offer,value-cost) for offer,value,floor,cost in rows if value>=floor]
    ranked=sorted(eligible,key=lambda x:(-x[1],x[0]))
    return {'ranked':ranked,'selected':ranked[0][0] if ranked else None,
            'below_reservation':sorted(offer for offer,value,floor,cost in rows if value<floor)}

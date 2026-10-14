"""Row 777: Justice - Upholds rights.

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


def review_declared_process_safeguards(rows):
    """Rows: (case_id, notice_given_bit, response_opportunity_bit,
    review_route_available_bit). Report missing supplied procedural safeguards.
    No legal rights determination, justice/fairness proof, case decision or
    legal advice. Fixed caller-bit checklist, not actual rights enforcement.
    """
    _rows(rows, 4)
    for case,notice,response,review in rows:
        _label(case)
        _integer(notice, 0, 1)
        _integer(response, 0, 1)
        _integer(review, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate case')
    cases=[]
    for case,notice,response,review in sorted(rows):
        missing=[]
        if notice==0:
            missing.append('notice')
        if response==0:
            missing.append('response_opportunity')
        if review==0:
            missing.append('review_route')
        cases.append((case,missing))
    return {'cases':cases,'cases_with_gaps':sum(bool(x[1]) for x in cases)}

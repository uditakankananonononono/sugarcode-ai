"""Row 714: Mediation - Facilitates agreement.

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


def review_joint_terms(rows):
    """Rows: (term_id, supplied_party_A_acceptance_bit,
    supplied_party_B_acceptance_bit). Partition joint terms into shared,
    disputed or jointly rejected. Caller acceptance bits not authenticated;
    no mediation conversation, legal agreement or actual consent established.
    Pure supplied-data checklist, all_shared requires every supplied term shared.
    """
    _rows(rows, 3)
    for term,a,b in rows:
        _label(term)
        _integer(a, 0, 1)
        _integer(b, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate term')
    shared=[]
    disputed=[]
    rejected=[]
    for term,a,b in sorted(rows):
        if a==1 and b==1:
            shared.append(term)
        elif a==0 and b==0:
            rejected.append(term)
        else:
            disputed.append(term)
    return {'shared':shared,'disputed':disputed,'jointly_rejected':rejected,
            'all_shared':len(shared)==len(rows)}

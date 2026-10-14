"""Row 752: Charitable Interpretation - Assumes good faith.

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


def select_supplied_reading(rows):
    """Rows: (interpretation_id, supplied_evidence_score, benign_bit,
    consistent_with_observed_facts_bit). Select fact-consistent interpretation
    by strongest evidence then benign preference then ID. No intent inference,
    language interpretation or good-faith certainty. Benign preference never
    overrides supplied inconsistency/evidence. All inconsistent yields None.
    """
    _rows(rows, 4)
    for interpretation,evidence,benign,consistent in rows:
        _label(interpretation)
        _integer(evidence, 0, 10)
        _integer(benign, 0, 1)
        _integer(consistent, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate interpretation')
    candidates=[x for x in rows if x[3]==1]
    ranked=sorted(candidates,key=lambda x:(-x[1],-x[2],x[0]))
    return {'ranked_candidates':[x[0] for x in ranked],
            'selected':ranked[0][0] if ranked else None,
            'excluded':sorted(x[0] for x in rows if x[3]==0)}

"""Row 750: Fallacy Detection - Spots flawed arguments.

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


def flag_supplied_argument_patterns(rows):
    """Rows: (argument_id, supplied_personal_attack_bit,
    unsupported_dilemma_bit, circular_support_bit). Flag declared patterns,
    NOT detect fallacies from language/logic or verify flags. Fixed suppliedbit
    checklist, absence of flags is not argument validity or soundness proof.
    """
    _rows(rows, 4)
    for argument,attack,dilemma,circular in rows:
        _label(argument)
        _integer(attack, 0, 1)
        _integer(dilemma, 0, 1)
        _integer(circular, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate argument')
    flags=[]
    for argument,attack,dilemma,circular in sorted(rows):
        patterns=[]
        if attack==1:
            patterns.append('personal_attack')
        if dilemma==1:
            patterns.append('unsupported_dilemma')
        if circular==1:
            patterns.append('circular_support')
        flags.append((argument,patterns))
    return {'arguments':flags,'flagged_count':sum(bool(x[1]) for x in flags)}

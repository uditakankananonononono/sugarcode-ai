"""Row 479: Organizational Design - Structures teams.

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


def structure_teams(rows):
    """Rows: (person_id, team_id, function_id), one team per person.

    Group the supplied roster and expose cross-functional teams. This is a
    descriptive structure, not a staffing recommendation or personnel action.
    """
    _rows(rows, 3)
    for person, team, function in rows:
        for value in (person, team, function):
            _label(value)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate person')
    teams = []
    for team in sorted({x[1] for x in rows}):
        members = sorted((person, function) for person, t, function in rows if t == team)
        functions = sorted({function for _, function in members})
        teams.append({'team': team, 'members': members, 'functions': functions,
                      'size': len(members), 'cross_functional': len(functions) > 1})
    return {'teams': teams, 'people': len(rows), 'team_count': len(teams)}

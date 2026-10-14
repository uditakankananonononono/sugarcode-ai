"""Row 526: Authorization Design - Controls access.

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


def evaluate_access(rows):
    """Rows: (subject, resource, action, grant_bit, explicit_deny_bit).
    Pure deny-overrides decision over supplied assertions. No live permissions,
    identity lookup, enforcement or authorization service integration.
    """
    _rows(rows, 5)
    for subject, resource, action, grant, deny in rows:
        for value in (subject, resource, action):
            _label(value)
        _integer(grant, 0, 1)
        _integer(deny, 0, 1)
    if len({(x[0],x[1],x[2]) for x in rows}) != len(rows):
        raise ValueError('duplicate request')
    return {'decisions': [(subject,resource,action,grant==1 and deny==0)
                          for subject,resource,action,grant,deny in sorted(rows)]}


def evaluate_role_policy(policy, requests):
    """Policy rows: (role, resource, action, effect), effect 'allow' or 'deny'.
    Request rows: (subject, role, resource, action).

    Exact-match role policy, deny overrides allow and absent rules deny. Roles are
    caller assertions. No identity/role store, inheritance, wildcards, deployed
    enforcement or actual authorization grant. Pure returned decisions only.
    """
    _rows(policy, 4)
    _rows(requests, 4)
    for role, resource, action, effect in policy:
        for value in (role, resource, action):
            _label(value)
        if type(effect) is not str:
            raise TypeError('exact string effect required')
        if effect not in ('allow', 'deny'):
            raise ValueError('effect must be allow or deny')
    for row in requests:
        for value in row:
            _label(value)
    if len(set(policy)) != len(policy):
        raise ValueError('duplicate policy rule')
    if len(set(requests)) != len(requests):
        raise ValueError('duplicate policy request')
    decisions = []
    for subject, role, resource, action in sorted(requests):
        effects = {effect for r, obj, act, effect in policy
                   if (r, obj, act) == (role, resource, action)}
        decisions.append((subject, role, resource, action,
                          'allow' in effects and 'deny' not in effects))
    return {'decisions': decisions}

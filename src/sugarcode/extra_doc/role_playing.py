"""Row 760, Role Playing: casting supplied roles to actors.

Practices perspectives by assignment. Each row pairs a role with an
actor, both strings of 1 to 8 characters; each role appears at most
once and each actor plays at most one role. Reported: the cast as
(role, actor) pairs in the order given and the cast size.
Caps (checked before any work): 0 to 50 rows.
NOT_CLAIMED: real role play, acting, improvisation, training,
facilitation, psychology, production readiness.
"""
SCOPE = 'PARTIAL: cast assignment over supplied rows, no real role play'
NOT_CLAIMED = ('real role play', 'acting', 'improvisation', 'training',
               'facilitation', 'psychology', 'production readiness')

MAX_ROWS = 50
MAX_NAME = 8


def assign(roles):
    if type(roles) not in (list, tuple):
        raise TypeError('roles must be a list or tuple')
    if len(roles) > MAX_ROWS:
        raise ValueError('roles must contain at most 50 rows')
    rows = []
    for row in roles:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each role must be a (role, actor) row')
        role, actor = row
        if type(role) is not str or not 1 <= len(role) <= MAX_NAME:
            raise ValueError('role must be a string of 1 to 8 characters')
        if type(actor) is not str or not 1 <= len(actor) <= MAX_NAME:
            raise ValueError('actor must be a string of 1 to 8 characters')
        rows.append((role, actor))
    seen_roles = set()
    seen_actors = set()
    for role, actor in rows:
        if role in seen_roles:
            raise ValueError('each role may appear only once')
        if actor in seen_actors:
            raise ValueError('each actor may play only one role')
        seen_roles.add(role)
        seen_actors.add(actor)
    return {'cast': rows, 'size': len(rows)}

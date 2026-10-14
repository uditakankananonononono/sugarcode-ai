"""Row 625, Feature Flags: deciding whether a flag is on for one user.

flags is a list or tuple of 1 to 30 (name, allow, deny, default) rows. For a
flag and a user the answer is: denied if the user is in deny, otherwise allowed
if the user is in allow, otherwise the default. Deny wins when a user is in
both lists. Reported: enabled (a bool) and the reason ('denied', 'allowed' or
'default').
Caps (checked before any work): flag names are unique strings of 1 to 16
characters, allow and deny are lists or tuples of at most 10 unique user names
of 1 to 16 characters, default is an exact bool, the asked flag must exist.
NOT_CLAIMED: percentage rollouts, targeting rules beyond two lists, remote
configuration, audit logs, flag expiry, production readiness.
"""
SCOPE = 'PARTIAL: allow and deny list lookup over supplied flag rows, no rollouts or remote config'
NOT_CLAIMED = ('percentage rollouts', 'targeting rules beyond two lists', 'remote configuration',
               'audit logs', 'flag expiry', 'production readiness')

MAX_FLAGS = 30
MAX_USERS = 10


def _name(v, msg):
    if type(v) is not str or not 1 <= len(v) <= 16:
        raise ValueError(msg)


def _users(v):
    if type(v) not in (list, tuple):
        raise ValueError('allow and deny must be lists or tuples')
    if len(v) > MAX_USERS or any(type(u) is not str or not 1 <= len(u) <= 16 for u in v) or len(set(v)) != len(v):
        raise ValueError('allow and deny must hold at most 10 unique names of 1 to 16 characters')


def flag_enabled(flags, flag, user):
    if type(flags) not in (list, tuple):
        raise TypeError('flags must be a list or tuple')
    if not 1 <= len(flags) <= MAX_FLAGS:
        raise ValueError('flags must contain between 1 and 30 entries')
    _name(flag, 'flag must be a string of 1 to 16 characters')
    _name(user, 'user must be a string of 1 to 16 characters')
    rows = {}
    for r in flags:
        if type(r) not in (list, tuple) or len(r) != 4:
            raise ValueError('each flag must be a (name, allow, deny, default) quadruple')
        name, allow, deny, default = r
        _name(name, 'flag names must be strings of 1 to 16 characters')
        _users(allow)
        _users(deny)
        if type(default) is not bool:
            raise ValueError('default must be a bool')
        if name in rows:
            raise ValueError('duplicate flag name')
        rows[name] = (allow, deny, default)
    if flag not in rows:
        raise ValueError('unknown flag')
    allow, deny, default = rows[flag]
    if user in deny:
        return {'enabled': False, 'reason': 'denied'}
    if user in allow:
        return {'enabled': True, 'reason': 'allowed'}
    return {'enabled': default, 'reason': 'default'}

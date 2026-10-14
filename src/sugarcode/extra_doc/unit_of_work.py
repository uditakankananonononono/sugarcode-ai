"""Row 670, Unit of Work (PARTIAL: one exact commit rule): batch registered changes and apply them all or none.

commit_unit_of_work(state, changes) takes the current records and a list of registered changes and returns what a single
commit would do. state is a dict of key -> int. Each change is a tuple (action, key, value) where action is 'new' (the key
must not exist yet), 'dirty' (the key must exist; its value becomes the given one) or 'removed' (the key must exist; the
value must be 0 and is ignored). Changes are checked in the order given against the state as earlier changes left it,
so 'new' then 'removed' on the same key cancels out, and 'removed' then 'new' replaces the value. If any change breaks a
rule the whole batch is refused and nothing changes. It returns:
  state       the records after the commit, sorted (key, value) pairs;
  inserts     keys that did not exist before and exist after, sorted;
  updates     keys that existed before and after with a different value, sorted;
  deletes     keys that existed before and not after, sorted;
  statements  the commit plan, in order: ('insert', key, value) by key, ('update', key, value) by key, ('delete', key, 0) by
              key; a key whose value is the same before and after has no statement.
Caps: state has 0 to 32 keys; 1 to 64 changes; keys are lowercase identifiers of 1 to 24 characters; values are nonbool ints
from -1000000 to 1000000.
Order of checks: state (type, size, each key and value in insertion order: key type, key shape, value type, value range), then
changes (list type, count, then each change in order: tuple type, 3 items, action type and name, key type and shape, value type
and range), and only then the change rules in order ('new' on an existing key, 'dirty' or 'removed' on a missing key, 'removed'
with a nonzero value); the first broken rule is reported.

NOT_CLAIMED: this is one in-memory rule on dictionaries. It does not touch a database, handle concurrency or isolation, retry,
order statements for foreign keys, or guarantee durability. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
LIM = 1000000
ACTIONS = ('new', 'dirty', 'removed')


def _key(k):
    if type(k) is not str:
        raise TypeError('key must be an exact string')
    if LABEL.fullmatch(k) is None:
        raise ValueError('key must be 1 to 24 lowercase identifier characters')


def _val(v):
    if type(v) is not int:
        raise TypeError('value must be a nonbool int')
    if not -LIM <= v <= LIM:
        raise ValueError('value must be between -1000000 and 1000000')


def commit_unit_of_work(state, changes):
    if type(state) is not dict:
        raise TypeError('state must be an exact dict')
    if len(state) > 32:
        raise ValueError('state must have at most 32 keys')
    for k, v in state.items():
        _key(k)
        _val(v)
    if type(changes) is not list:
        raise TypeError('changes must be an exact list')
    if not 1 <= len(changes) <= 64:
        raise ValueError('change count must be between 1 and 64')
    for c in changes:
        if type(c) is not tuple:
            raise TypeError('each change must be an exact tuple')
        if len(c) != 3:
            raise ValueError('each change must have 3 items')
        if type(c[0]) is not str:
            raise TypeError('action must be an exact string')
        if c[0] not in ACTIONS:
            raise ValueError("action must be 'new', 'dirty' or 'removed'")
        _key(c[1])
        _val(c[2])
    now = dict(state)
    for action, key, value in changes:
        if action == 'new':
            if key in now:
                raise ValueError('new: key already exists')
            now[key] = value
        elif action == 'dirty':
            if key not in now:
                raise ValueError('dirty: key does not exist')
            now[key] = value
        else:
            if key not in now:
                raise ValueError('removed: key does not exist')
            if value != 0:
                raise ValueError('removed: value must be 0')
            del now[key]
    inserts = sorted(k for k in now if k not in state)
    updates = sorted(k for k in now if k in state and now[k] != state[k])
    deletes = sorted(k for k in state if k not in now)
    statements = ([('insert', k, now[k]) for k in inserts] + [('update', k, now[k]) for k in updates]
                  + [('delete', k, 0) for k in deletes])
    return {'state': sorted(now.items()), 'inserts': inserts, 'updates': updates, 'deletes': deletes,
            'statements': statements}

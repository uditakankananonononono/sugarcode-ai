"""Row 683, Functional Core, Imperative Shell (PARTIAL: one exact purity rule): check that effects stay out of the core.

check_purity(functions, calls, effects) takes functions as a list of (name, zone), zone 'core' or 'shell', calls as a list of
(caller, callee), and effects as a list of the function names that do an effect (read a file, write, use the clock, ...). It
returns:
  core_calls_shell  sorted (caller, callee) for each call from a core function to a shell function;
  core_effects      sorted core function names that are listed in effects;
  tainted           sorted core function names from which a listed effect function can be reached by zero or more calls
                    (a core function that is listed in effects itself is tainted too).
A design is clean in this table when all three lists are empty.
Caps: 1 to 32 functions with unique names, 0 to 96 calls without duplicates, 0 to 32 effects without repeats; every name must
be among the functions. Names are 1 to 24 lowercase identifier characters.
Order of checks: functions (list type, count, then each in order: tuple type, 2 items, name type and shape, zone type and
value), duplicate name, calls (list type, count, then each in order: tuple type, 2 items, caller name type and shape, callee
type and shape), duplicate call, unknown name in calls (caller before callee, in order), effects (list type, count, then each
name type and shape), repeated effect, unknown name in effects, and only then the analysis.

NOT_CLAIMED: this checks a supplied table. It does not read code, find real effects, or say that a core is truly pure or a shell
thin. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _name(v):
    if type(v) is not str:
        raise TypeError('name must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError('name must be 1 to 24 lowercase identifier characters')


def check_purity(functions, calls, effects):
    if type(functions) is not list:
        raise TypeError('functions must be an exact list')
    if not 1 <= len(functions) <= 32:
        raise ValueError('function count must be between 1 and 32')
    for f in functions:
        if type(f) is not tuple:
            raise TypeError('each function must be an exact tuple')
        if len(f) != 2:
            raise ValueError('each function must have 2 items')
        _name(f[0])
        if type(f[1]) is not str:
            raise TypeError('zone must be an exact string')
        if f[1] not in ('core', 'shell'):
            raise ValueError("zone must be 'core' or 'shell'")
    zone = dict(functions)
    if len(zone) != len(functions):
        raise ValueError('duplicate function name')
    if type(calls) is not list:
        raise TypeError('calls must be an exact list')
    if len(calls) > 96:
        raise ValueError('call count must be at most 96')
    for c in calls:
        if type(c) is not tuple:
            raise TypeError('each call must be an exact tuple')
        if len(c) != 2:
            raise ValueError('each call must have 2 items')
        _name(c[0])
        _name(c[1])
    if len(set(calls)) != len(calls):
        raise ValueError('duplicate call')
    for a, b in calls:
        if a not in zone:
            raise ValueError('unknown function: ' + a)
        if b not in zone:
            raise ValueError('unknown function: ' + b)
    if type(effects) is not list:
        raise TypeError('effects must be an exact list')
    if len(effects) > 32:
        raise ValueError('effect count must be at most 32')
    for e in effects:
        _name(e)
    if len(set(effects)) != len(effects):
        raise ValueError('repeated effect')
    for e in effects:
        if e not in zone:
            raise ValueError('unknown function: ' + e)
    out = {n: [b for a, b in calls if a == n] for n in zone}
    tainted = []
    for n in zone:
        if zone[n] != 'core':
            continue
        seen = set()
        todo = [n]
        while todo:
            x = todo.pop()
            if x not in seen:
                seen.add(x)
                todo.extend(out[x])
        if seen & set(effects):
            tainted.append(n)
    return {'core_calls_shell': sorted((a, b) for a, b in calls if zone[a] == 'core' and zone[b] == 'shell'),
            'core_effects': sorted(e for e in effects if zone[e] == 'core'), 'tainted': sorted(tainted)}

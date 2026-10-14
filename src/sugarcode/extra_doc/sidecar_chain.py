"""Row 659, Sidecar Pattern: a chain of sidecar steps around a supplied value.

sidecar_chain takes value, a nonbool int from -1000 to 1000, and steps, a
list or tuple of 0 to 8 (kind, arg) pairs. kind is 'add', 'scale', 'cap' or
'floor'; arg is a nonbool int from -100 to 100. Steps apply in order: add
gives value + arg, scale gives value * arg, cap gives the smaller of value
and arg, floor gives the larger. Reported: result, trace (the value after
each step) and changed (how many steps changed the value).
Checks, in this order: value, steps type, steps size, then each step (pair
shape, kind, arg).
NOT_CLAIMED: real proxies, processes, networking, service meshes,
production readiness.
"""
SCOPE = 'PARTIAL: ordered sidecar steps over one supplied value, no real proxy'
NOT_CLAIMED = ('real proxies', 'processes', 'networking', 'service meshes',
               'production readiness')

KINDS = ('add', 'scale', 'cap', 'floor')
MAX_STEPS = 8


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def sidecar_chain(value, steps):
    _int(value, -1000, 1000, 'value must be a nonbool integer between -1000 and 1000')
    if type(steps) not in (list, tuple):
        raise TypeError('steps must be a list or tuple')
    if len(steps) > MAX_STEPS:
        raise ValueError('steps must contain at most 8 entries')
    for s in steps:
        if type(s) not in (list, tuple) or len(s) != 2:
            raise ValueError('each step must be a (kind, arg) pair')
        kind, arg = s
        if type(kind) is not str or kind not in KINDS:
            raise ValueError('kind must be add, scale, cap or floor')
        _int(arg, -100, 100, 'arg must be a nonbool integer between -100 and 100')
    trace = []
    changed = 0
    cur = value
    for kind, arg in steps:
        if kind == 'add':
            new = cur + arg
        elif kind == 'scale':
            new = cur * arg
        elif kind == 'cap':
            new = min(cur, arg)
        else:
            new = max(cur, arg)
        if new != cur:
            changed += 1
        cur = new
        trace.append(cur)
    return {'result': cur, 'trace': trace, 'changed': changed}

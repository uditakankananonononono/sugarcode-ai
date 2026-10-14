"""Row 694, Legacy Code Modernization: dependency-ordered modernization waves.

modernization_waves takes modules, a list or tuple of 1 to max_modules
(name, deps) pairs, and max_modules, a nonbool int from 1 to 20 (default 6). A name is a
string of 1 to 12 characters, distinct across modules. deps is a list or
tuple of names (at most 4, each a listed module other than itself, no
repeats). A module joins the first wave after every dependency has been
modernized, so wave 0 holds the modules without dependencies. Inside a wave
modules keep input order.
Returns waves (list of lists of names) and order (all names, wave by wave).
Checks, in this order: max_modules, modules type, modules size, each pair
(shape, name, deps), duplicate names, dependencies (unknown, self), cycle.
NOT_CLAIMED: real dependency analysis, code quality, migration effort,
rewrite success, production readiness.
"""
SCOPE = 'PARTIAL: topological wave ordering of supplied module dependencies, no code is analysed'
NOT_CLAIMED = ('real dependency analysis', 'code quality', 'migration effort',
               'rewrite success', 'production readiness')


def modernization_waves(modules, max_modules=6):
    if type(max_modules) is not int or not 1 <= max_modules <= 20:
        raise ValueError('max_modules must be a nonbool integer between 1 and 20')
    if type(modules) not in (list, tuple):
        raise TypeError('modules must be a list or tuple')
    if not 1 <= len(modules) <= max_modules:
        raise ValueError('modules must contain 1 to max_modules entries')
    rows = []
    for mo in modules:
        if type(mo) not in (list, tuple) or len(mo) != 2:
            raise ValueError('each module must be a (name, deps) pair')
        name, deps = mo
        if type(name) is not str or not 1 <= len(name) <= 12:
            raise ValueError('each name must be a string of 1 to 12 characters')
        if type(deps) not in (list, tuple) or len(deps) > 4:
            raise ValueError('deps must be a list or tuple of at most 4 names')
        rows.append((name, deps))
    names = [r[0] for r in rows]
    if len(set(names)) != len(names):
        raise ValueError('names must be distinct')
    for name, deps in rows:
        for d in deps:
            if type(d) is not str or d not in names:
                raise ValueError('each dependency must be a listed module')
            if d == name:
                raise ValueError('a module cannot depend on itself')
        if len(set(deps)) != len(deps):
            raise ValueError('dependencies must not repeat')
    done = set()
    waves = []
    todo = list(rows)
    while todo:
        wave = [n for n, deps in todo if all(d in done for d in deps)]
        if not wave:
            raise ValueError('dependency cycle detected')
        waves.append(wave)
        done.update(wave)
        todo = [(n, deps) for n, deps in todo if n not in done]
    return {'waves': waves, 'order': [n for w in waves for n in w]}

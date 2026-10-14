"""Row 515 Monolith Design: exact coupling table for a caller-described module dependency graph.

The caller supplies 1 to 12 unique modules (name, lines, depends_on): lines an int 0 to 10**7 and
depends_on the distinct names of other modules it uses (never itself). Reported per module: fan-out
(modules it uses), fan-in (modules using it), its share of all lines (Fraction, None when total
lines is 0) and whether it sits on a dependency cycle (it can reach itself through the graph).
Also: the modules on cycles in input order, the largest module (first on ties), and the number of
dependency edges. Caps are implementation choices, not spec values. Nothing is parsed from code;
the graph is the caller's.
NOT_CLAIMED: that the graph matches any real code base, that the line counts are measured, that a
module boundary is good or bad, that fan-in, fan-out or cycles predict maintainability, that a
monolith or any other architecture is the right choice, approval-gate clearance, deployment.
"""
from fractions import Fraction

NOT_CLAIMED = ('graph matches any real code base', 'line counts measured', 'a module boundary good or bad',
               'fan-in, fan-out or cycles predict maintainability', 'a monolith or any architecture is the right choice',
               'approval-gate clearance', 'deployment')


def analyse_modules(modules):
    if type(modules) not in (list, tuple):
        raise TypeError('modules must be a list or tuple')
    if not 1 <= len(modules) <= 12:
        raise ValueError('module count must be between 1 and 12')
    names = []
    for m in modules:
        if type(m) not in (list, tuple) or len(m) != 3:
            raise ValueError('each module must be (name, lines, depends_on)')
        if type(m[0]) is not str:
            raise TypeError('names must be str')
        if not 1 <= len(m[0]) <= 40:
            raise ValueError('names must be 1 to 40 characters')
        names.append(m[0])
    if len(set(names)) != len(names):
        raise ValueError('module names must be unique')
    rows = []
    for name, lines, deps in modules:
        if type(lines) is not int:
            raise TypeError('lines must be nonbool int')
        if not 0 <= lines <= 10 ** 7:
            raise ValueError('lines must be between 0 and 10000000')
        if type(deps) not in (list, tuple):
            raise TypeError('depends_on must be a list or tuple')
        if len(deps) >= len(names):
            raise ValueError('depends_on names too many modules')
        for d in deps:
            if type(d) is not str:
                raise TypeError('depends_on must hold str names')
            if d not in names:
                raise ValueError('depends_on names an unknown module')
            if d == name:
                raise ValueError('a module cannot depend on itself')
        if len(set(deps)) != len(deps):
            raise ValueError('depends_on must not repeat a name')
        rows.append((name, lines, frozenset(deps)))
    reach = {r[0]: set(r[2]) for r in rows}
    changed = True
    while changed:
        changed = False
        for a in reach:
            new = set().union(*(reach[b] for b in reach[a])) - reach[a] if reach[a] else set()
            if new:
                reach[a] |= new
                changed = True
    total = sum(r[1] for r in rows)
    per = [{'name': n, 'fan_out': len(d), 'fan_in': sum(1 for r in rows if n in r[2]),
            'line_share': Fraction(l, total) if total else None, 'on_cycle': n in reach[n]} for n, l, d in rows]
    big = max(range(len(rows)), key=lambda i: (rows[i][1], -i))
    return {'modules': per, 'cyclic_modules': tuple(p['name'] for p in per if p['on_cycle']),
            'largest_module': rows[big][0], 'edge_count': sum(len(r[2]) for r in rows),
            'design_validated': False, 'not_claimed': NOT_CLAIMED}

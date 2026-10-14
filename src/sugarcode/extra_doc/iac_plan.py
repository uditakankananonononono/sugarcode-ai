"""Row 612, Infrastructure as Code (PARTIAL: one exact step of a plan): what to create, update and delete, and in what order.

plan_changes(current, desired) compares two resource lists. A resource is a tuple (name, spec, deps): name a lowercase
identifier, spec a nonbool int (the declared setting, compared by equality), deps a tuple of the names it depends on
(at most 8, no duplicates, each present in the same list, never itself, no cycles). It returns:
  create     names only in desired;
  update     names in both whose spec differs or whose set of dependencies differs;
  unchanged  names in both with the same spec and the same set of dependencies;
  delete     names only in current;
  order      the whole desired list in the smallest dependency order (the lexicographically smallest list in which
             every resource comes after all it depends on); create and update follow this order;
  delete_order  delete names, dependents first: the reverse of the smallest dependency order of the current list.
delete and unchanged are in name order.
Caps: each list is a list of 0 to 32 tuples with 3 items; spec from -1000000 to 1000000.
Order of checks: current, then desired. For each list: the list type and size, then each row in order (tuple type,
3 items, name, spec, deps type, deps count, each dep name), then duplicate names, then a duplicated dependency in row order, then unknown dependencies in row order,
then a self dependency in row order, then a cycle. Messages begin with the list name (current or desired). Only then
the comparison.

NOT_CLAIMED: this is a plan on supplied declarations only. It does not read or change any real infrastructure,
detect drift from the real world, run a provider, check that a spec is valid for anything, or apply the plan.
No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
MAX_ROWS = 32
MAX_DEPS = 8


def _label(v, what):
    if type(v) is not str:
        raise TypeError(what + ': name must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError(what + ': name must be 1 to 24 lowercase identifier characters')


def _order(rows):
    deps = {n: set(d) for n, _, d in rows}
    left = set(deps)
    out = []
    while left:
        ready = sorted(n for n in left if deps[n] <= set(out))
        if not ready:
            return None
        out.append(ready[0])
        left.discard(ready[0])
    return out


def _check(rows, what):
    if type(rows) is not list:
        raise TypeError(what + ': must be an exact list')
    if len(rows) > MAX_ROWS:
        raise ValueError(what + ': at most 32 resources')
    parsed = []
    for row in rows:
        if type(row) is not tuple:
            raise TypeError(what + ': resource must be an exact tuple')
        if len(row) != 3:
            raise ValueError(what + ': resource must have 3 items')
        name, spec, deps = row
        _label(name, what)
        if type(spec) is not int:
            raise TypeError(what + ': spec must be a nonbool int')
        if not -1000000 <= spec <= 1000000:
            raise ValueError(what + ': spec must be between -1000000 and 1000000')
        if type(deps) is not tuple:
            raise TypeError(what + ': deps must be an exact tuple')
        if len(deps) > MAX_DEPS:
            raise ValueError(what + ': at most 8 deps')
        for d in deps:
            _label(d, what)
        parsed.append((name, spec, deps))
    names = [r[0] for r in parsed]
    if len(set(names)) != len(names):
        raise ValueError(what + ': duplicate name')
    for name, _, deps in parsed:
        if len(set(deps)) != len(deps):
            raise ValueError(what + ': duplicate dependency')
    for name, _, deps in parsed:
        for d in deps:
            if d not in names:
                raise ValueError(what + ': unknown dependency')
    for name, _, deps in parsed:
        if name in deps:
            raise ValueError(what + ': resource depends on itself')
    order = _order(parsed)
    if order is None:
        raise ValueError(what + ': dependency cycle')
    return parsed, order


def plan_changes(current, desired):
    cur, cur_order = _check(current, 'current')
    des, des_order = _check(desired, 'desired')
    c = {n: (s, frozenset(d)) for n, s, d in cur}
    d = {n: (s, frozenset(x)) for n, s, x in des}
    create = [n for n in des_order if n not in c]
    update = [n for n in des_order if n in c and c[n] != d[n]]
    unchanged = sorted(n for n in d if n in c and c[n] == d[n])
    gone = {n for n in c if n not in d}
    delete = sorted(gone)
    delete_order = [n for n in reversed(cur_order) if n in gone]
    return {'create': create, 'update': update, 'unchanged': unchanged,
            'delete': delete, 'order': des_order, 'delete_order': delete_order}

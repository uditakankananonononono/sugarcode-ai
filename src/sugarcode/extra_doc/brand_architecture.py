"""Row 403, Brand Architecture (Bounded: one exact tree rule): check a supplied brand-to-parent table.

check_brands(brands) takes brands as a list of 0 to 20 tuples (name, parent): name 1 to 24 lowercase identifier
characters, parent either None (a root) or a name of the same shape. The rules, applied to each entry i (0-based):
  a name already used by an earlier entry, else (i, 'same_name');
  a parent equal to its own name, else (i, 'self_parent');
  a parent that is not the name of any entry, else (i, 'missing_parent').
It returns {'problems': sorted (index, code), 'roots': names of entries with parent None in input order,
'depths': sorted (name, depth) pairs for entries whose chain reaches a root without a rule break on the way (root depth 0),
'max_depth': the largest such depth or 0}. Entries with a cycle or a broken chain have no depth.
Order of checks: brands (list type, count, then each in order: tuple type, 2 items, name type and shape, parent
None or type and shape), and only then the rules.

NOT_CLAIMED: this checks a supplied table. It does not say the structure suits any portfolio or that names are good.
No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _name(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError(what + ' must be 1 to 24 lowercase identifier characters')


def check_brands(brands):
    if type(brands) is not list:
        raise TypeError('brands must be an exact list')
    if len(brands) > 20:
        raise ValueError('brand count must be at most 20')
    for b in brands:
        if type(b) is not tuple:
            raise TypeError('each brand must be an exact tuple')
        if len(b) != 2:
            raise ValueError('each brand must have 2 items')
        _name(b[0], 'name')
        if b[1] is not None:
            _name(b[1], 'parent')
    problems, seen = [], set()
    allnames = {b[0] for b in brands}
    for i, (n, p) in enumerate(brands):
        if n in seen:
            problems.append((i, 'same_name'))
        seen.add(n)
        if p == n:
            problems.append((i, 'self_parent'))
        elif p is not None and p not in allnames:
            problems.append((i, 'missing_parent'))
    parent = {}
    for n, p in brands:
        parent.setdefault(n, p)
    depths = {}
    for n in parent:
        path, cur = [], n
        while cur in parent and cur not in path:
            path.append(cur)
            if parent[cur] is None:
                depths[n] = len(path) - 1
                break
            cur = parent[cur]
    return {'problems': sorted(problems), 'roots': [n for n, p in brands if p is None],
            'depths': sorted(depths.items()), 'max_depth': max(depths.values(), default=0)}

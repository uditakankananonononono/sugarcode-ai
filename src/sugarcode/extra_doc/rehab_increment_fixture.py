"""Row 1140, Rehabilitation Planning.

rehab_increment_fixture uses supplied quota x and completed count y.
Allocate up to budget to remaining deficits in label order, without exceeding
any deficit. Returns allocations as sorted (label,allocated_count), unused
as leftover budget, unfilled as sorted (label,remaining_deficit). Abstract
quota accounting only, not a rehabilitation regimen or clinical plan.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
budget defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, budget, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: rehabilitation plan, medical efficacy, task suitability, patient applicability, production readiness.
"""

SCOPE = 'PARTIAL: apportions a supplied integer practice budget by fixed per-task quotas, no rehabilitation is planned'
NOT_CLAIMED = ('rehabilitation plan', 'medical efficacy', 'task suitability', 'patient applicability', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def rehab_increment_fixture(rows, budget=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(budget) is not int or not 0 <= budget <= 10:
        raise ValueError('budget must be a nonbool integer between 0 and 10')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    allocations = []
    left = budget
    for n, quota, completed in sorted(clean, key=lambda r: r[0]):
        needed = max(0, quota - completed)
        take = min(left, needed)
        allocations.append((n, take))
        left -= take
    return {'allocations': allocations, 'unused': left,
            'unfilled': [(n, max(0, quota-completed-take)) for (n, quota, completed), (m, take) in zip(sorted(clean, key=lambda r: r[0]), allocations)]}

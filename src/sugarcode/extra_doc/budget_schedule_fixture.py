"""Row 1148, Addiction Treatment Planning.

budget_schedule_fixture allocates budget units in ascending label order.
Each supplied task needs max(0,x-y), where x is requested units and y is
already reserved units. Returns allocations (label,given,missing), unused
budget and complete (every missing count zero). Units are abstract and this
does not design, recommend or validate addiction treatment.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
budget defaults to 7, an exact int from 0 to 80.
Validation order: rows type, rows size, budget, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: addiction treatment, clinical prioritization, dose or care plan, safety, production readiness.
"""

SCOPE = 'PARTIAL: allocates abstract unit budgets to supplied tasks, no addiction treatment planning'
NOT_CLAIMED = ('addiction treatment', 'clinical prioritization', 'dose or care plan', 'safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def budget_schedule_fixture(rows, budget=7):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(budget) is not int or not 0 <= budget <= 80:
        raise ValueError('budget must be a nonbool integer between 0 and 80')
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
    left = budget
    allocations = []
    for n, requested, reserve in sorted(clean, key=lambda r:r[0]):
        need = max(0, requested - reserve)
        given = min(left, need)
        left -= given
        allocations.append((n, given, need - given))
    return {'allocations': allocations, 'unused': left,
            'complete': all(missing == 0 for n, given, missing in allocations)}

"""Row 574, Optimization Engine: exact best selection of items under one weight limit (0/1 knapsack).

best_selection(items, capacity) takes items as (weight, value) pairs and a weight limit, picks each item at most once,
and returns, exactly:
  value     the largest total value of any selection whose total weight is at most capacity;
  weight    the smallest total weight among the selections that reach that value;
  chosen    the item positions (counting from 0, increasing) of one such selection: among the selections with that
            value and weight, the one whose position list reads smallest from the left (position 0 first).
Caps: items a list or tuple of 0 to 20 pairs (lists or tuples of two nonbool ints); weight 1 to 1000; value 0 to
1000000; capacity a nonbool int from 0 to 10000.
Order of checks: items (type, count, then each pair in order: shape, weight type, value type, weight range, value range),
then capacity (type, range), and only then the search. The search is a dynamic programme over (item position,
remaining capacity), so the answer is exact, not heuristic.

NOT_CLAIMED: arithmetic on the numbers supplied only. It does not say the weights and values describe anything real, that
value adds up across items, that the limit is the only constraint, or that a larger total value is better in
practice; no item can be split. No clinical or wet-lab claim.
"""

MAX_ITEMS = 20
MAX_WEIGHT = 1000
MAX_VALUE = 1000000
MAX_CAP = 10000


def _int(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be a nonbool int')
    return v


def best_selection(items, capacity):
    if type(items) not in (list, tuple):
        raise TypeError('items must be a list or tuple')
    if not 0 <= len(items) <= MAX_ITEMS:
        raise ValueError('item count must be between 0 and 20')
    its = []
    for p in items:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise TypeError('each item must be a (weight, value) pair')
        w = _int(p[0], 'weight')
        v = _int(p[1], 'value')
        if not 1 <= w <= MAX_WEIGHT:
            raise ValueError('weight must be between 1 and 1000')
        if not 0 <= v <= MAX_VALUE:
            raise ValueError('value must be between 0 and 1000000')
        its.append((w, v))
    cap = _int(capacity, 'capacity')
    if not 0 <= cap <= MAX_CAP:
        raise ValueError('capacity must be between 0 and 10000')
    n = len(its)
    # table[i][c] = (best value, minus its weight) using items i.. with room c; larger tuples are better
    table = [[(0, 0)] * (cap + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        w, v = its[i]
        row, nxt = table[i], table[i + 1]
        for c in range(cap + 1):
            best = nxt[c]
            if c >= w:
                bv, bw = nxt[c - w]
                take = (bv + v, bw - w)
                if take >= best:
                    best = take
            row[c] = best
    chosen, c = [], cap
    for i in range(n):
        w, v = its[i]
        if c >= w:
            bv, bw = table[i + 1][c - w]
            if (bv + v, bw - w) == table[i][c]:
                chosen.append(i)
                c -= w
    value, minus_w = table[0][cap]
    return {'value': value, 'weight': -minus_w, 'chosen': chosen}

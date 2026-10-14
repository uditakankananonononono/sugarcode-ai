"""Row 329, Furniture Design: exact cut list and tip-over check for a piece of furniture.

cut_plan(parts, stock_mm, kerf_mm) says how few stock boards of length stock_mm are needed to
cut every part (lengths in mm) when each saw cut wastes kerf_mm. A board holding parts p1..pk
uses sum(p) + kerf_mm * k millimetres (one cut after each part, including the last, which
trims the end); it must not exceed stock_mm. The result is the exact minimum number of boards
(found by backtracking, so it is optimal, not a heuristic), one lexicographically smallest
assignment (part index to board number, boards numbered by first use), each board's parts
and waste (stock - used), and the total waste.
tip_check(base_mm, height_mm, load_height_mm, load_offset_mm) is a plain static test for a
free-standing piece: the load must sit over the base (load_offset_mm from the centre is at most
base_mm / 2; the margin base_mm / 2 - load_offset_mm is an exact Fraction) and no higher than the
piece (load_height_mm <= height_mm). It returns the margin, both booleans and stable (both true).
Caps: 1 to 12 parts of 1 to 5000 mm, stock 1 to 10000 mm, kerf 0 to 20 mm; base 1 to 5000, height
1 to 5000, load height 0 to 5000 and offset 0 to 5000 mm. All values nonbool int. cut_plan checks
parts (container, count, then each length's type), then the types of stock and kerf, then the ranges,
then that every part plus its kerf fits a fresh board (a named error), and only then searches.
tip_check checks all four types, then the ranges in argument order.

NOT_CLAIMED: arithmetic only. No joinery strength, wood grain, moisture movement, load rating, safety
certification, ergonomics, style or comfort judgement; the tip check ignores the weight of the
piece, friction and dynamic loads. No clinical or wet-lab claim.
"""
from fractions import Fraction

MAX_PARTS = 12


def _int(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be a nonbool int')


def cut_plan(parts, stock_mm, kerf_mm):
    if type(parts) not in (list, tuple):
        raise TypeError('parts must be a list or tuple')
    if not 1 <= len(parts) <= MAX_PARTS:
        raise ValueError('part count must be between 1 and 12')
    for p in parts:
        _int(p, 'part length')
    _int(stock_mm, 'stock_mm')
    _int(kerf_mm, 'kerf_mm')
    for p in parts:
        if not 1 <= p <= 5000:
            raise ValueError('part length must be between 1 and 5000 mm')
    if not 1 <= stock_mm <= 10000:
        raise ValueError('stock_mm must be between 1 and 10000')
    if not 0 <= kerf_mm <= 20:
        raise ValueError('kerf_mm must be between 0 and 20')
    cost = [p + kerf_mm for p in parts]
    if max(cost) > stock_mm:
        raise ValueError('a part plus its kerf is longer than the stock board')
    limit = max(1, -(-sum(cost) // stock_mm))
    while True:
        asg = _lex_smallest(cost, stock_mm, limit)
        if asg is not None:
            break
        limit += 1
    boards = [[] for _ in range(limit)]
    for i, b in enumerate(asg):
        boards[b].append(i)
    used = [sum(cost[i] for i in bd) for bd in boards]
    return {'boards': limit, 'assignment': asg, 'board_parts': boards,
            'waste_mm': [stock_mm - u for u in used], 'total_waste_mm': stock_mm * limit - sum(used)}


def _lex_smallest(cost, stock, limit):
    n = len(cost)
    load = [0] * limit
    asg = [0] * n

    def rec(i, used):
        if i == n:
            return True
        for b in range(min(used + 1, limit)):
            if load[b] + cost[i] <= stock:
                load[b] += cost[i]
                asg[i] = b
                if rec(i + 1, max(used, b + 1)):
                    return True
                load[b] -= cost[i]
        return False
    return asg if rec(0, 0) else None


def tip_check(base_mm, height_mm, load_height_mm, load_offset_mm):
    for v, nm in ((base_mm, 'base_mm'), (height_mm, 'height_mm'), (load_height_mm, 'load_height_mm'),
                  (load_offset_mm, 'load_offset_mm')):
        _int(v, nm)
    if not 1 <= base_mm <= 5000:
        raise ValueError('base_mm must be between 1 and 5000')
    if not 1 <= height_mm <= 5000:
        raise ValueError('height_mm must be between 1 and 5000')
    if not 0 <= load_height_mm <= 5000:
        raise ValueError('load_height_mm must be between 0 and 5000')
    if not 0 <= load_offset_mm <= 5000:
        raise ValueError('load_offset_mm must be between 0 and 5000')
    margin = Fraction(base_mm, 2) - load_offset_mm
    return {'margin_mm': margin, 'load_over_base': margin >= 0, 'load_within_height': load_height_mm <= height_mm,
            'stable': margin >= 0 and load_height_mm <= height_mm}

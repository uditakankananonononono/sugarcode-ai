"""Row 435, Price Elasticity Analysis (PARTIAL: one exact movement rule): check a supplied observation list.

check_moves(moves) takes moves as a list of 0 to 40 tuples (product, price_delta, demand_delta): product 1 to 24
lowercase identifier characters, price_delta and demand_delta exact integers -100 to 100 (percent changes). The
rules, applied to each observation i (0-based), are:
  price_delta and demand_delta are both nonzero with the same sign, else (i, 'same_sign');
  price_delta is 0 and demand_delta is not, else (i, 'phantom_shift').
It returns {'problems': sorted (index, code), 'products': sorted distinct products present, 'total': the move
count}.
Order of checks: moves (list type, count, then each in order: tuple type, 3 items, product type and shape,
price_delta type and range, demand_delta type and range), and only then the rules.

NOT_CLAIMED: this checks supplied percent changes against two sign rules. It does not measure elasticity, and it
does not say the changes were real or that any customer responded. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_moves(moves):
    if type(moves) is not list:
        raise TypeError('moves must be an exact list')
    if len(moves) > 40:
        raise ValueError('move count must be at most 40')
    for s in moves:
        if type(s) is not tuple:
            raise TypeError('each move must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each move must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('product must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('product must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('price_delta must be an exact integer')
        if not -100 <= s[1] <= 100:
            raise ValueError('price_delta must be -100 to 100')
        if type(s[2]) is not int:
            raise TypeError('demand_delta must be an exact integer')
        if not -100 <= s[2] <= 100:
            raise ValueError('demand_delta must be -100 to 100')
    problems = []
    names = set()
    for i, (product, price_delta, demand_delta) in enumerate(moves):
        if price_delta * demand_delta > 0:
            problems.append((i, 'same_sign'))
        if price_delta == 0 and demand_delta != 0:
            problems.append((i, 'phantom_shift'))
        names.add(product)
    return {'problems': sorted(problems), 'products': sorted(names), 'total': len(moves)}

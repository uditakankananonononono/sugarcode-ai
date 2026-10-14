"""Row 434, Pricing Strategy (PARTIAL: one exact price-band rule): check a supplied product-price list.

check_prices(prices) takes prices as a list of 0 to 40 tuples (product, cost, price): product 1 to 24 lowercase
identifier characters, cost and price exact integers 0 to 1000000 (cents). The rules, applied to each product i
(0-based), are:
  price below cost, else (i, 'below_cost');
  price more than five times cost, else (i, 'markup_high'); a zero cost never raises markup_high.
It returns {'problems': sorted (index, code), 'products': sorted distinct products present, 'total': the product
count}.
Order of checks: prices (list type, count, then each in order: tuple type, 3 items, product type and shape, cost
type and range, price type and range), and only then the rules.

NOT_CLAIMED: this checks supplied prices against two band bars. It does not say the prices are optimal, that five
times cost is the right cap, or that anything sold. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_prices(prices):
    if type(prices) is not list:
        raise TypeError('prices must be an exact list')
    if len(prices) > 40:
        raise ValueError('price count must be at most 40')
    for s in prices:
        if type(s) is not tuple:
            raise TypeError('each price must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each price must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('product must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('product must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('cost must be an exact integer')
        if not 0 <= s[1] <= 1000000:
            raise ValueError('cost must be 0 to 1000000')
        if type(s[2]) is not int:
            raise TypeError('price must be an exact integer')
        if not 0 <= s[2] <= 1000000:
            raise ValueError('price must be 0 to 1000000')
    problems = []
    names = set()
    for i, (product, cost, price) in enumerate(prices):
        if price < cost:
            problems.append((i, 'below_cost'))
        if cost > 0 and price > 5 * cost:
            problems.append((i, 'markup_high'))
        names.add(product)
    return {'problems': sorted(problems), 'products': sorted(names), 'total': len(prices)}

"""Row 444, Cross-Selling (PARTIAL: one exact pair rule): check a supplied product-pair list.

check_pairs(pairs) takes pairs as a list of 0 to 40 tuples (anchor, addon, lift): anchor and addon 1 to 24
lowercase identifier characters, lift an exact integer -100 to 1000 (percent change in addon attach rate when
anchored). The rules, applied to each pair i (0-based), are:
  anchor equals addon, else (i, 'self_pair');
  lift below 5, else (i, 'weak_pair').
It returns {'problems': sorted (index, code), 'products': sorted distinct products present, 'total': the pair
count}.
Order of checks: pairs (list type, count, then each in order: tuple type, 3 items, anchor type and shape, addon
type and shape, lift type and range), and only then the rules.

NOT_CLAIMED: this checks supplied pairs against two fit bars. It does not say the pairs sell complementary
products, that 5 percent is the right lift bar, or that any basket grew. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_pairs(pairs):
    if type(pairs) is not list:
        raise TypeError('pairs must be an exact list')
    if len(pairs) > 40:
        raise ValueError('pair count must be at most 40')
    for s in pairs:
        if type(s) is not tuple:
            raise TypeError('each pair must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each pair must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('anchor must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('anchor must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not str:
            raise TypeError('addon must be an exact string')
        if LABEL.fullmatch(s[1]) is None:
            raise ValueError('addon must be 1 to 24 lowercase identifier characters')
        if type(s[2]) is not int:
            raise TypeError('lift must be an exact integer')
        if not -100 <= s[2] <= 1000:
            raise ValueError('lift must be -100 to 1000')
    problems = []
    names = set()
    for i, (anchor, addon, lift) in enumerate(pairs):
        if anchor == addon:
            problems.append((i, 'self_pair'))
        if lift < 5:
            problems.append((i, 'weak_pair'))
        names.add(anchor)
        names.add(addon)
    return {'problems': sorted(problems), 'products': sorted(names), 'total': len(pairs)}

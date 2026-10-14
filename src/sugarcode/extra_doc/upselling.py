"""Row 443, Upselling (PARTIAL: one exact upgrade-step rule): check a supplied upgrade-offer list.

check_offers(offers) takes offers as a list of 0 to 40 tuples (offer, current_cents, target_cents): offer 1 to
24 lowercase identifier characters, current_cents and target_cents exact integers 0 to 1000000. The rules,
applied to each offer i (0-based), are:
  target_cents at or below current_cents, else (i, 'no_upgrade');
  target_cents more than triple current_cents, else (i, 'too_steep'); a zero current never raises too_steep.
It returns {'problems': sorted (index, code), 'offers': sorted distinct offers present, 'total': the offer
count}.
Order of checks: offers (list type, count, then each in order: tuple type, 3 items, offer type and shape,
current_cents type and range, target_cents type and range), and only then the rules.

NOT_CLAIMED: this checks supplied offers against two step bars. It does not say the offers increase order value,
that triple is the right step, or that any customer accepted. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_offers(offers):
    if type(offers) is not list:
        raise TypeError('offers must be an exact list')
    if len(offers) > 40:
        raise ValueError('offer count must be at most 40')
    for s in offers:
        if type(s) is not tuple:
            raise TypeError('each offer must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each offer must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('offer must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('offer must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('current_cents must be an exact integer')
        if not 0 <= s[1] <= 1000000:
            raise ValueError('current_cents must be 0 to 1000000')
        if type(s[2]) is not int:
            raise TypeError('target_cents must be an exact integer')
        if not 0 <= s[2] <= 1000000:
            raise ValueError('target_cents must be 0 to 1000000')
    problems = []
    names = set()
    for i, (offer, current_cents, target_cents) in enumerate(offers):
        if target_cents <= current_cents:
            problems.append((i, 'no_upgrade'))
        if current_cents > 0 and target_cents > 3 * current_cents:
            problems.append((i, 'too_steep'))
        names.add(offer)
    return {'problems': sorted(problems), 'offers': sorted(names), 'total': len(offers)}

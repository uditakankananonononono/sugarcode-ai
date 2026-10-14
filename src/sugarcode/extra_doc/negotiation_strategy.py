"""Row 432, Negotiation Strategy (PARTIAL: one exact concession rule): check a supplied item-concession list.

check_plan(items) takes items as a list of 0 to 40 tuples (item, level, concession): item 1 to 24 lowercase
identifier characters, level an exact string 'must', 'want' or 'give', concession an exact integer 0 to 100
(percent of the item's value that can be given up). The rules, applied to each item i (0-based), are:
  level 'must' with concession over 0, else (i, 'must_concedes');
  level 'give' with concession under 20, else (i, 'give_tight').
It returns {'problems': sorted (index, code), 'items': sorted distinct items present, 'total': the item count}.
Order of checks: items (list type, count, then each in order: tuple type, 3 items, item type and shape, level
type and membership, concession type and range), and only then the rules.

NOT_CLAIMED: this checks a supplied plan against two concession bars. It does not say the negotiation is planned
well, that must-haves should never concede, or that any deal was reached. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
LEVELS = ('must', 'want', 'give')


def check_plan(items):
    if type(items) is not list:
        raise TypeError('items must be an exact list')
    if len(items) > 40:
        raise ValueError('item count must be at most 40')
    for s in items:
        if type(s) is not tuple:
            raise TypeError('each item must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each item must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('item must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('item must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not str:
            raise TypeError('level must be an exact string')
        if s[1] not in LEVELS:
            raise ValueError('level must be must, want or give')
        if type(s[2]) is not int:
            raise TypeError('concession must be an exact integer')
        if not 0 <= s[2] <= 100:
            raise ValueError('concession must be 0 to 100')
    problems = []
    names = set()
    for i, (item, level, concession) in enumerate(items):
        if level == 'must' and concession > 0:
            problems.append((i, 'must_concedes'))
        if level == 'give' and concession < 20:
            problems.append((i, 'give_tight'))
        names.add(item)
    return {'problems': sorted(problems), 'items': sorted(names), 'total': len(items)}

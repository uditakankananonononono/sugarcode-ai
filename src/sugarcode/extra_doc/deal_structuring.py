"""Row 433, Deal Structuring (PARTIAL: one exact tranche-sum rule): check a supplied payment-tranche list.

check_tranches(tranches) takes tranches as a list of 0 to 40 tuples (tranche, percent): tranche 1 to 24 lowercase
identifier characters, percent an exact integer 0 to 100 (share of the deal value). The rules, applied to each
tranche i (0-based) in supplied order, are:
  the running sum of percents including this one exceeds 100, else (i, 'over_full');
  percent is 0, else (i, 'empty').
It returns {'problems': sorted (index, code), 'tranches': sorted distinct tranches present, 'funded': the summed
percent, 'total': the tranche count}.
Order of checks: tranches (list type, count, then each in order: tuple type, 2 items, tranche type and shape,
percent type and range), and only then the rules.

NOT_CLAIMED: this checks supplied tranche shares against one sum bar. It does not say the agreement is designed
well, that 100 is the right total, or that any payment was made. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_tranches(tranches):
    if type(tranches) is not list:
        raise TypeError('tranches must be an exact list')
    if len(tranches) > 40:
        raise ValueError('tranche count must be at most 40')
    for s in tranches:
        if type(s) is not tuple:
            raise TypeError('each tranche must be an exact tuple')
        if len(s) != 2:
            raise ValueError('each tranche must have 2 items')
        if type(s[0]) is not str:
            raise TypeError('tranche must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('tranche must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('percent must be an exact integer')
        if not 0 <= s[1] <= 100:
            raise ValueError('percent must be 0 to 100')
    problems = []
    names = set()
    running = 0
    for i, (tranche, percent) in enumerate(tranches):
        running += percent
        if running > 100:
            problems.append((i, 'over_full'))
        if percent == 0:
            problems.append((i, 'empty'))
        names.add(tranche)
    return {'problems': sorted(problems), 'tranches': sorted(names), 'funded': running, 'total': len(tranches)}

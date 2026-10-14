"""Row 437, Subscription Design (PARTIAL: one exact tier-ladder rule): check a supplied tier list.

check_tiers(tiers) takes tiers as a list of 0 to 40 tuples (tier, monthly_cents): tier 1 to 24 lowercase
identifier characters, monthly_cents an exact integer 0 to 1000000. The rules, applied to each tier i (0-based)
in supplied order, are:
  monthly_cents at or below the immediately previous tier's, else (i, 'not_dearer');
  monthly_cents over ten times the immediately previous tier's when that tier is nonzero, else (i, 'gap_wide').
The first tier cannot raise either. It returns {'problems': sorted (index, code), 'tiers': sorted distinct tiers
present, 'total': the tier count}.
Order of checks: tiers (list type, count, then each in order: tuple type, 2 items, tier type and shape,
monthly_cents type and range), and only then the rules.

NOT_CLAIMED: this checks a supplied ladder against two spacing bars. It does not say the tiers create recurring
revenue, that ten times is the right gap, or that anyone subscribed. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_tiers(tiers):
    if type(tiers) is not list:
        raise TypeError('tiers must be an exact list')
    if len(tiers) > 40:
        raise ValueError('tier count must be at most 40')
    for s in tiers:
        if type(s) is not tuple:
            raise TypeError('each tier must be an exact tuple')
        if len(s) != 2:
            raise ValueError('each tier must have 2 items')
        if type(s[0]) is not str:
            raise TypeError('tier must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('tier must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('monthly_cents must be an exact integer')
        if not 0 <= s[1] <= 1000000:
            raise ValueError('monthly_cents must be 0 to 1000000')
    problems = []
    names = set()
    previous = None
    for i, (tier, monthly_cents) in enumerate(tiers):
        if previous is not None:
            if monthly_cents <= previous:
                problems.append((i, 'not_dearer'))
            elif previous > 0 and monthly_cents > 10 * previous:
                problems.append((i, 'gap_wide'))
        names.add(tier)
        previous = monthly_cents
    return {'problems': sorted(problems), 'tiers': sorted(names), 'total': len(tiers)}

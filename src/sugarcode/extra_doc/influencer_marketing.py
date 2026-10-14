"""Row 421, Influencer Marketing (Bounded: one exact budget rule): check a supplied influencer deal list against a budget.

check_deals(budget, deals) takes budget as an exact int 0 to 1000000 and deals as a list of 0 to 20 tuples
(handle, fee, reach): handle 1 to 24 lowercase identifier characters, fee an exact int 0 to 1000000, reach an exact
int 1 to 100000000. The rules: a handle already used by an earlier deal, else (i, 'same_handle'); a fee above 100 per
1000 reach (fee*10 > reach), else (i, 'pricey'). If the fee total exceeds budget, the code ('over_budget') is returned
in 'gaps'. It returns {'problems': sorted (index, code), 'gaps': ['over_budget'] or [], 'spend': fee total, 'reach':
reach total, 'left': budget minus spend}.
Order of checks: budget (type, range), deals (list type, count, then each in order: tuple type, 3 items, handle type
and shape, fee type and range, reach type and range), and only then the rules.

NOT_CLAIMED: this checks supplied numbers. It does not say the reach is real, that the price cap fits any market, or that
the deals would pay back. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _int(v, lo, hi, what):
    if type(v) is not int:
        raise TypeError(what + ' must be an exact int')
    if not lo <= v <= hi:
        raise ValueError(what + ' must be %d to %d' % (lo, hi))


def check_deals(budget, deals):
    _int(budget, 0, 1000000, 'budget')
    if type(deals) is not list:
        raise TypeError('deals must be an exact list')
    if len(deals) > 20:
        raise ValueError('deal count must be at most 20')
    for d in deals:
        if type(d) is not tuple:
            raise TypeError('each deal must be an exact tuple')
        if len(d) != 3:
            raise ValueError('each deal must have 3 items')
        if type(d[0]) is not str:
            raise TypeError('handle must be an exact string')
        if LABEL.fullmatch(d[0]) is None:
            raise ValueError('handle must be 1 to 24 lowercase identifier characters')
        _int(d[1], 0, 1000000, 'fee')
        _int(d[2], 1, 100000000, 'reach')
    problems, seen = [], set()
    for i, (h, fee, reach) in enumerate(deals):
        if h in seen:
            problems.append((i, 'same_handle'))
        seen.add(h)
        if fee * 10 > reach:
            problems.append((i, 'pricey'))
    spend = sum(d[1] for d in deals)
    return {'problems': sorted(problems), 'gaps': ['over_budget'] if spend > budget else [], 'spend': spend,
            'reach': sum(d[2] for d in deals), 'left': budget - spend}

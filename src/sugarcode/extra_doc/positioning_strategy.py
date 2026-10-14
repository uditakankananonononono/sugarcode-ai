"""Row 402, Positioning Strategy (Bounded: one exact margin rule): compare supplied own and rival attribute ratings.

check_positions(attrs) takes attrs as a list of 0 to 10 tuples (attribute, ours, rival): attribute 1 to 24 lowercase
identifier characters, ours and rival exact ints 0 to 10. Margin is ours minus rival. Verdict per attribute: 'win' at
margin 2 or more, 'lag' at margin -2 or less, else 'tie'. An attribute name already used by an earlier entry is reported
as (i, 'same_attribute'). It returns {'problems': sorted (index, code), 'verdicts': one code per entry in input order,
'margins': per entry, 'wins': names of win entries sorted, 'net': sum of margins}.
Order of checks: attrs (list type, count, then each in order: tuple type, 3 items, attribute type and shape, ours type
and range, rival type and range), and only then the rules.

NOT_CLAIMED: this compares supplied ratings. It does not say the ratings are measured, that the thresholds fit a market,
or that the position claims mental space. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _int(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be an exact int')
    if not 0 <= v <= 10:
        raise ValueError(what + ' must be 0 to 10')


def check_positions(attrs):
    if type(attrs) is not list:
        raise TypeError('attrs must be an exact list')
    if len(attrs) > 10:
        raise ValueError('attribute count must be at most 10')
    for a in attrs:
        if type(a) is not tuple:
            raise TypeError('each attribute must be an exact tuple')
        if len(a) != 3:
            raise ValueError('each attribute must have 3 items')
        name, ours, rival = a
        if type(name) is not str:
            raise TypeError('attribute must be an exact string')
        if LABEL.fullmatch(name) is None:
            raise ValueError('attribute must be 1 to 24 lowercase identifier characters')
        _int(ours, 'ours')
        _int(rival, 'rival')
    problems, seen, verdicts, margins = [], set(), [], []
    for i, (name, ours, rival) in enumerate(attrs):
        m = ours - rival
        margins.append(m)
        verdicts.append('win' if m >= 2 else 'lag' if m <= -2 else 'tie')
        if name in seen:
            problems.append((i, 'same_attribute'))
        seen.add(name)
    return {'problems': problems, 'verdicts': verdicts, 'margins': margins,
            'wins': sorted(attrs[i][0] for i, v in enumerate(verdicts) if v == 'win'), 'net': sum(margins)}

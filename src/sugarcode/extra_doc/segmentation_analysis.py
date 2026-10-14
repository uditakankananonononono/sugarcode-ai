"""Row 400, Segmentation Analysis (PARTIAL: one exact table rule): check that supplied segments divide a customer list.

check_segments(segments) takes segments as a list of 0 to 12 tuples (name, members): name 1 to 24 lowercase identifier
characters, members a list of 0 to 50 member ids of the same shape. The rules, applied to each segment i (0-based), are:
  no members, else (i, 'empty');
  fewer than 4 members, else (i, 'below_floor');
  a member repeated inside the segment, else (i, 'repeat');
  a member already listed in an earlier segment, else (i, 'overlap') - reported once per segment;
  a name already used by an earlier segment, else (i, 'same_name').
One segment can break several rules; all are reported. It returns {'problems': sorted (index, code), 'sizes': sorted
(name, member count) pairs, 'shared': sorted member ids that appear in two or more segments, 'total': the number of
distinct member ids}.
Order of checks: segments (list type, count, then each in order: tuple type, 2 items, name type and shape, members list
type, member count, then each member in order: type and shape), and only then the rules.

NOT_CLAIMED: this checks a supplied table. It does not say the segments are meaningful, that the floor of 4 fits the
market, or that dividing customers this way helps. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _name(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError(what + ' must be 1 to 24 lowercase identifier characters')


def check_segments(segments):
    if type(segments) is not list:
        raise TypeError('segments must be an exact list')
    if len(segments) > 12:
        raise ValueError('segment count must be at most 12')
    for s in segments:
        if type(s) is not tuple:
            raise TypeError('each segment must be an exact tuple')
        if len(s) != 2:
            raise ValueError('each segment must have 2 items')
        _name(s[0], 'name')
        if type(s[1]) is not list:
            raise TypeError('members must be an exact list')
        if len(s[1]) > 50:
            raise ValueError('member count must be at most 50')
        for m in s[1]:
            _name(m, 'member')
    problems = []
    sizes = []
    seen_names = set()
    seen_members = set()
    owners = {}
    for i, (name, members) in enumerate(segments):
        sizes.append((name, len(members)))
        if name in seen_names:
            problems.append((i, 'same_name'))
        seen_names.add(name)
        if not members:
            problems.append((i, 'empty'))
        elif len(members) < 4:
            problems.append((i, 'below_floor'))
        if len(set(members)) != len(members):
            problems.append((i, 'repeat'))
        if any(m in seen_members for m in members):
            problems.append((i, 'overlap'))
        seen_members.update(members)
        for m in set(members):
            owners.setdefault(m, set()).add(i)
    return {'problems': sorted(problems), 'sizes': sorted(sizes),
            'shared': sorted(m for m in owners if len(owners[m]) >= 2), 'total': len(owners)}

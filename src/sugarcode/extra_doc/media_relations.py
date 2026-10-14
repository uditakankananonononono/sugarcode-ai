"""Row 417, Media Relations (PARTIAL: one exact tracker rule): check a supplied outreach log for order and blanketing.

check_outreach(entries) takes entries as a list of 0 to 40 tuples (journalist, outlet, status): journalist and outlet
1 to 24 lowercase identifier characters, status one of 'pitched', 'replied', 'published', 'declined' (exact strings),
whose stages are 0, 1, 2, 2. The rules, applied to each entry i (0-based), are:
  the journalist's stage drops below the highest stage they reached on any earlier entry, else (i, 'out_of_order');
  the journalist is the third or later distinct contact for the outlet, else (i, 'blanketing').
It returns {'problems': sorted (index, code), 'published': sorted outlets with at least one published entry, 'total':
the entry count}.
Order of checks: entries (list type, count, then each in order: tuple type, 3 items, journalist type and shape, outlet
type and shape, status type and value), and only then the rules.

NOT_CLAIMED: this checks a supplied log against one stage order. It does not say the pitches were good, that three
contacts is spam, or that any journalist replied. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
STAGE = {name: rank for rank, name in enumerate(('pitched', 'replied', 'published'))}
STAGE['declined'] = STAGE['published']


def _name(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError(what + ' must be 1 to 24 lowercase identifier characters')


def check_outreach(entries):
    if type(entries) is not list:
        raise TypeError('entries must be an exact list')
    if len(entries) > 40:
        raise ValueError('entry count must be at most 40')
    for e in entries:
        if type(e) is not tuple:
            raise TypeError('each entry must be an exact tuple')
        if len(e) != 3:
            raise ValueError('each entry must have 3 items')
        _name(e[0], 'journalist')
        _name(e[1], 'outlet')
        if type(e[2]) is not str:
            raise TypeError('status must be an exact string')
        if e[2] not in STAGE:
            raise ValueError('status must be one of: declined, pitched, published, replied')
    problems = []
    best_stage = {}
    outlet_contacts = {}
    published = set()
    for i, (journalist, outlet, status) in enumerate(entries):
        stage = STAGE[status]
        previous = best_stage.get(journalist)
        if previous is not None and stage < previous:
            problems.append((i, 'out_of_order'))
        best_stage[journalist] = stage if previous is None else max(previous, stage)
        contacts = outlet_contacts.setdefault(outlet, set())
        if journalist not in contacts and len(contacts) >= 2:
            problems.append((i, 'blanketing'))
        contacts.add(journalist)
        if status == 'published':
            published.add(outlet)
    return {'problems': sorted(problems), 'published': sorted(published), 'total': len(entries)}

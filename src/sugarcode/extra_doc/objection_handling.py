"""Row 431, Objection Handling (PARTIAL: one exact reply-age rule): check a supplied objection-reply list.

check_replies(replies) takes replies as a list of 0 to 40 tuples (objection, minutes, outcome): objection 1 to 24
lowercase identifier characters, minutes an exact integer 0 to 10080 (age of the objection), outcome an exact
string 'resolved', 'deflected' or 'open'. The rules, applied to each reply i (0-based), are:
  minutes over 240, else (i, 'slow_reply');
  outcome still 'open' with minutes over 1440, else (i, 'stale_open').
It returns {'problems': sorted (index, code), 'objections': sorted distinct objections present, 'total': the
reply count}.
Order of checks: replies (list type, count, then each in order: tuple type, 3 items, objection type and shape,
minutes type and range, outcome type and membership), and only then the rules.

NOT_CLAIMED: this checks a supplied reply list against two age bars. It does not say the concerns were addressed,
that 240 or 1440 minutes are the right bars, or that any customer was satisfied. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
OUTCOMES = ('resolved', 'deflected', 'open')


def check_replies(replies):
    if type(replies) is not list:
        raise TypeError('replies must be an exact list')
    if len(replies) > 40:
        raise ValueError('reply count must be at most 40')
    for s in replies:
        if type(s) is not tuple:
            raise TypeError('each reply must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each reply must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('objection must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('objection must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('minutes must be an exact integer')
        if not 0 <= s[1] <= 10080:
            raise ValueError('minutes must be 0 to 10080')
        if type(s[2]) is not str:
            raise TypeError('outcome must be an exact string')
        if s[2] not in OUTCOMES:
            raise ValueError('outcome must be resolved, deflected or open')
    problems = []
    names = set()
    for i, (objection, minutes, outcome) in enumerate(replies):
        if minutes > 240:
            problems.append((i, 'slow_reply'))
        if outcome == 'open' and minutes > 1440:
            problems.append((i, 'stale_open'))
        names.add(objection)
    return {'problems': sorted(problems), 'objections': sorted(names), 'total': len(replies)}

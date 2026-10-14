"""Row 420, Community Management (Bounded: one exact response rule): check a supplied post queue against reply limits.

check_queue(posts) takes posts as a list of 0 to 30 tuples (posted, replied): posted an exact int minute 0 to 100000,
replied an exact int minute 0 to 100000 or None (no reply yet). The rules, per post i (0-based): replied before posted,
else (i, 'time_travel'); replied more than 60 minutes after posted, else (i, 'slow'); no reply, else (i, 'unanswered').
It returns {'problems': sorted (index, code), 'answered': count of posts with a reply that is not time_travel,
'waits': sorted waits (replied minus posted) of answered posts, 'longest': the largest wait or 0}.
Order of checks: posts (list type, count, then each in order: tuple type, 2 items, posted type and range, replied None
or type and range), and only then the rules.

NOT_CLAIMED: this checks supplied timestamps. It does not say the replies were helpful, that the 60 minute limit suits a
community, or that members are satisfied. No clinical or wet-lab claim.
"""


def _int(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be an exact int')
    if not 0 <= v <= 100000:
        raise ValueError(what + ' must be 0 to 100000')


def check_queue(posts):
    if type(posts) is not list:
        raise TypeError('posts must be an exact list')
    if len(posts) > 30:
        raise ValueError('post count must be at most 30')
    for p in posts:
        if type(p) is not tuple:
            raise TypeError('each post must be an exact tuple')
        if len(p) != 2:
            raise ValueError('each post must have 2 items')
        _int(p[0], 'posted')
        if p[1] is not None:
            _int(p[1], 'replied')
    problems, waits = [], []
    for i, (a, b) in enumerate(posts):
        if b is None:
            problems.append((i, 'unanswered'))
        elif b < a:
            problems.append((i, 'time_travel'))
        else:
            waits.append(b - a)
            if b - a > 60:
                problems.append((i, 'slow'))
    waits.sort()
    return {'problems': sorted(problems), 'answered': len(waits), 'waits': waits,
            'longest': waits[-1] if waits else 0}

"""Row 692, Mob Programming: turn plan for a mob on one problem.

mob_turns takes members, a list or tuple of 3 to 8 distinct names (strings of 1
to 12 characters), total_minutes, a nonbool int from 1 to 240, and
turn_minutes, a nonbool int from 1 to 30 (default 10). Turn i (from 0) starts
at i * turn_minutes, ends at the smaller of start + turn_minutes and
total_minutes, and is driven by members[i % n]. Turns continue until
total_minutes is covered.
Returns turns ((index, driver, start, end) per turn) and minutes ((name,
driven minutes) in members order).
Checks, in this order: members type, members size, each name, duplicate names,
total_minutes, turn_minutes.
NOT_CLAIMED: mob quality, real attendance, code quality, team fit,
production readiness.
"""
SCOPE = 'PARTIAL: round-robin turn plan from supplied names and minutes, no mob session runs'
NOT_CLAIMED = ('mob quality', 'real attendance', 'code quality',
               'team fit', 'production readiness')


def mob_turns(members, total_minutes, turn_minutes=10):
    if type(members) not in (list, tuple):
        raise TypeError('members must be a list or tuple')
    if not 3 <= len(members) <= 8:
        raise ValueError('members must contain 3 to 8 entries')
    for p in members:
        if type(p) is not str or not 1 <= len(p) <= 12:
            raise ValueError('each name must be a string of 1 to 12 characters')
    if len(set(members)) != len(members):
        raise ValueError('names must be distinct')
    if type(total_minutes) is not int or not 1 <= total_minutes <= 240:
        raise ValueError('total_minutes must be a nonbool integer between 1 and 240')
    if type(turn_minutes) is not int or not 1 <= turn_minutes <= 30:
        raise ValueError('turn_minutes must be a nonbool integer between 1 and 30')
    n = len(members)
    turns = []
    mins = [0] * n
    start = 0
    i = 0
    while start < total_minutes:
        end = min(start + turn_minutes, total_minutes)
        turns.append((i, members[i % n], start, end))
        mins[i % n] += end - start
        start = end
        i += 1
    return {'turns': turns, 'minutes': [(members[k], mins[k]) for k in range(n)]}

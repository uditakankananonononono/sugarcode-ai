"""Row 647, Cron Jobs: next run times for a five-field cron expression.

Fields: minute (0-59), hour (0-23), day of month (1-31), month (1-12), day of
week (0-6, 0 is Sunday). Each field is a comma list of: *, */n, a, or a-b. When
both day-of-month and day-of-week fields start with *, or neither does, the
usual rule applies: if neither starts with * a day matches when EITHER matches,
otherwise BOTH must match. Returns the next count run times strictly after
start (seconds ignored), searching at most 1461 days ahead; exhausted is True
when fewer than count were found.
Caps (checked before any work): expression string of at most 64 characters with
five fields, start a naive datetime in 2000 to 2099, count 1 to 20 (nonbool int).
NOT_CLAIMED: time zones and DST, names like MON or JAN, @-macros, seconds,
the L W # extensions, running anything, production readiness.
"""
import datetime

SCOPE = 'PARTIAL: five numeric cron fields with lists, ranges and steps, naive datetimes'
NOT_CLAIMED = ('time zones and DST', 'month or weekday names', '@ macros', 'seconds',
               'L W # extensions', 'running anything', 'production readiness')
LIMITS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))


def _num(s, lo, hi):
    if not (s.isascii() and s.isdigit() and len(s) <= 2) or not lo <= int(s) <= hi:
        raise ValueError('invalid cron field')
    return int(s)


def _field(text, lo, hi):
    out = set()
    for part in text.split(','):
        if part == '*':
            out.update(range(lo, hi + 1))
        elif part.startswith('*/'):
            step = _num(part[2:], 1, hi - lo + 1)
            out.update(range(lo, hi + 1, step))
        elif '-' in part:
            a, _, b = part.partition('-')
            a, b = _num(a, lo, hi), _num(b, lo, hi)
            if a > b:
                raise ValueError('invalid cron field')
            out.update(range(a, b + 1))
        else:
            out.add(_num(part, lo, hi))
    return out


def next_runs(expression, start, count):
    if type(expression) is not str:
        raise TypeError('expression must be a string')
    if len(expression) > 64:
        raise ValueError('expression must be at most 64 characters')
    parts = expression.split(' ')
    if len(parts) != 5:
        raise ValueError('expression must have five fields')
    if type(start) is not datetime.datetime:
        raise TypeError('start must be a datetime')
    if start.tzinfo is not None:
        raise ValueError('start must be naive')
    if not 2000 <= start.year <= 2099:
        raise ValueError('start year must be between 2000 and 2099')
    if type(count) is not int or not 1 <= count <= 20:
        raise ValueError('count must be a nonbool integer between 1 and 20')
    minute, hour, dom, month, dow = (_field(p, lo, hi) for p, (lo, hi) in zip(parts, LIMITS))
    dom_star, dow_star = parts[2].startswith('*'), parts[4].startswith('*')
    floor = start.replace(second=0, microsecond=0)
    runs = []
    for k in range(1462):
        day = (floor + datetime.timedelta(days=k)).date()
        weekday = (day.weekday() + 1) % 7
        if day.month not in month:
            continue
        by_dom, by_dow = day.day in dom, weekday in dow
        ok = (by_dom and by_dow) if (dom_star or dow_star) else (by_dom or by_dow)
        if not ok:
            continue
        for h in sorted(hour):
            for mi in sorted(minute):
                cand = datetime.datetime(day.year, day.month, day.day, h, mi)
                if cand > floor:
                    runs.append(cand)
                    if len(runs) == count:
                        return {'runs': runs, 'exhausted': False}
    return {'runs': runs, 'exhausted': True}

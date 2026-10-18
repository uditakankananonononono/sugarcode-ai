"""b427-new, proleptic Gregorian calendar arithmetic.

Ten pure functions over exact ints, years 1 to 9999, no time zones, no clocks,
no retrieval, no network, no files, no floats. Day numbers ("rata die") count
days with 0001-01-01 as day 1. Weekdays are 0 for Monday through 6 for Sunday
except in iso_week_date, which uses the ISO values 1 for Monday to 7 for Sunday.
Date arguments are validated in the order y, m, d, each type before range, then
the day against the month length. For two dates the first is fully validated
before the second.
NOT_CLAIMED: Julian or any other historical calendar, time zones, leap seconds,
local holiday rules other than the Western Easter date, production readiness.
"""

SCOPE = 'PARTIAL: exact proleptic Gregorian date arithmetic on supplied ints for years 1..9999, no historical calendar claim'
NOT_CLAIMED = ('julian or other historical calendars', 'time zones', 'leap seconds',
               'holidays other than western easter date', 'production readiness')
CLAIMS = {'theorem_proved': False, 'production_ready': False}

MIN_YEAR = 1
MAX_YEAR = 9999
MAX_RATA = 3652059
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _int(x, name):
    if isinstance(x, bool):
        raise TypeError(name + ' must not be a bool')
    if type(x) is not int:
        raise TypeError(name + ' must be an int')
    return x


def _year(y, name='y'):
    _int(y, name)
    if not MIN_YEAR <= y <= MAX_YEAR:
        raise ValueError(name + ' must be between 1 and 9999')
    return y


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _dim(y, m):
    return 29 if m == 2 and _leap(y) else _DAYS[m - 1]


def _date(y, m, d, suffix=''):
    _year(y, 'y' + suffix)
    _int(m, 'm' + suffix)
    if not 1 <= m <= 12:
        raise ValueError('m' + suffix + ' must be between 1 and 12')
    _int(d, 'd' + suffix)
    if not 1 <= d <= 31:
        raise ValueError('d' + suffix + ' must be between 1 and 31')
    if d > _dim(y, m):
        raise ValueError('day does not exist in that month')
    return y, m, d


def _doy(y, m, d):
    return sum(_DAYS[:m - 1]) + (1 if m > 2 and _leap(y) else 0) + d


def _rd(y, m, d):
    p = y - 1
    return 365 * p + p // 4 - p // 100 + p // 400 + _doy(y, m, d)


def _from_rd(n):
    n0 = n - 1
    c400, r = divmod(n0, 146097)
    c100, r = divmod(r, 36524)
    if c100 == 4:
        c100, r = 3, r + 36524
    c4, r = divmod(r, 1461)
    c1, r = divmod(r, 365)
    if c1 == 4:
        c1, r = 3, r + 365
    y = 400 * c400 + 100 * c100 + 4 * c4 + c1 + 1
    day = r + 1
    m = 1
    while day > _dim(y, m):
        day -= _dim(y, m)
        m += 1
    return y, m, day


def is_leap_year(y):
    """True iff y is a Gregorian leap year."""
    return _leap(_year(y))


def days_in_month(y, m):
    """Number of days in month m of year y."""
    _year(y)
    _int(m, 'm')
    if not 1 <= m <= 12:
        raise ValueError('m must be between 1 and 12')
    return _dim(y, m)


def day_of_year(y, m, d):
    """Ordinal day within the year, 1 to 366."""
    return _doy(*_date(y, m, d))


def date_from_day_of_year(y, n):
    """(year, month, day) for the n-th day of year y."""
    _year(y)
    _int(n, 'n')
    if not 1 <= n <= (366 if _leap(y) else 365):
        raise ValueError('n must be between 1 and the number of days in the year')
    m = 1
    while n > _dim(y, m):
        n -= _dim(y, m)
        m += 1
    return (y, m, n)


def rata_die(y, m, d):
    """Day number with 0001-01-01 equal to 1."""
    return _rd(*_date(y, m, d))


def date_from_rata_die(n):
    """(year, month, day) for a day number from 1 to 3652059."""
    _int(n, 'n')
    if not 1 <= n <= MAX_RATA:
        raise ValueError('n must be between 1 and 3652059')
    return _from_rd(n)


def weekday(y, m, d):
    """0 for Monday through 6 for Sunday."""
    return (_rd(*_date(y, m, d)) - 1) % 7


def iso_week_date(y, m, d):
    """(ISO year, ISO week 1..53, ISO weekday 1..7).

    The Thursday of the date's week always lies inside the supported range
    because day 1 is a Monday and the last supported day is a Friday.
    """
    y, m, d = _date(y, m, d)
    rd = _rd(y, m, d)
    wd = (rd - 1) % 7
    thursday = rd - wd + 3
    ty = _from_rd(thursday)[0]
    return (ty, (thursday - _rd(ty, 1, 1)) // 7 + 1, wd + 1)


def days_between(y1, m1, d1, y2, m2, d2):
    """Signed number of days from the first date to the second."""
    a = _date(y1, m1, d1, '1')
    b = _date(y2, m2, d2, '2')
    return _rd(*b) - _rd(*a)


def easter_sunday(y):
    """(month, day) of Western Easter Sunday, anonymous Gregorian computus."""
    _year(y)
    a = y % 19
    b, c = divmod(y, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    mm = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * mm + 114, 31)
    return (month, day + 1)

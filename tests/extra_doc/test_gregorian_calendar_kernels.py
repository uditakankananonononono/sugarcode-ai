import datetime
import random

import pytest

from sugarcode.extra_doc import gregorian_calendar_kernels as m
from sugarcode.extra_doc.gregorian_calendar_kernels import (
    is_leap_year, days_in_month, day_of_year, date_from_day_of_year, rata_die,
    date_from_rata_die, weekday, iso_week_date, days_between, easter_sunday)

D = datetime.date


def raises(exc, msg, f, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


def sample_dates(seed, n):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        y = rng.choice([rng.randint(1, 9999), rng.randint(1890, 2110), rng.choice([1, 4, 100, 400, 1600, 1900, 2000, 2100, 9996, 9999])])
        m_ = rng.randint(1, 12)
        d = rng.randint(1, m._dim(y, m_))
        out.append((y, m_, d))
    return out


def test_metadata():
    assert m.SCOPE.startswith('PARTIAL')
    assert m.NOT_CLAIMED and all(type(x) is str for x in m.NOT_CLAIMED)
    assert m.CLAIMS == {'theorem_proved': False, 'production_ready': False}
    assert (m.MIN_YEAR, m.MAX_YEAR, m.MAX_RATA) == (1, 9999, 3652059)
    assert m.MAX_RATA == D(9999, 12, 31).toordinal()


def test_known():
    assert [is_leap_year(y) for y in (1900, 2000, 2024, 2100, 1, 4)] == [False, True, True, False, False, True]
    assert days_in_month(2024, 2) == 29 and days_in_month(2023, 2) == 28
    assert day_of_year(2024, 12, 31) == 366 and day_of_year(2023, 3, 1) == 60
    assert date_from_day_of_year(2024, 60) == (2024, 2, 29)
    assert rata_die(1, 1, 1) == 1 and rata_die(2000, 1, 1) == 730120
    assert date_from_rata_die(1) == (1, 1, 1) and date_from_rata_die(3652059) == (9999, 12, 31)
    assert weekday(2000, 1, 1) == 5 and weekday(1, 1, 1) == 0
    assert iso_week_date(2021, 1, 3) == (2020, 53, 7) and iso_week_date(2018, 12, 31) == (2019, 1, 1)
    assert days_between(2000, 1, 1, 2000, 3, 1) == 60 and days_between(2000, 3, 1, 2000, 1, 1) == -60
    assert easter_sunday(2024) == (3, 31) and easter_sunday(2025) == (4, 20)


def test_every_day_roundtrip_range():
    # every day of every year 1..9999 would be 3.6M; check all days of 1..30, 1895..2105 and sampled elsewhere
    years = list(range(1, 31)) + list(range(1895, 2106)) + [399, 400, 401, 499, 500, 1599, 1600, 1700, 1800, 1900, 9998, 9999]
    for y in years:
        d0 = D(y, 1, 1)
        for k in range(366 if m._leap(y) else 365):
            d = d0 + datetime.timedelta(days=k)
            t = (d.year, d.month, d.day)
            assert rata_die(*t) == d.toordinal()
            assert date_from_rata_die(d.toordinal()) == t
            assert day_of_year(*t) == k + 1
            assert date_from_day_of_year(y, k + 1) == t
            assert weekday(*t) == d.weekday()
            assert iso_week_date(*t) == tuple(d.isocalendar())


@pytest.mark.parametrize('seed', range(5))
def test_random_dates(seed):
    pts = sample_dates(seed, 3000)
    for t in pts:
        d = D(*t)
        assert rata_die(*t) == d.toordinal()
        assert date_from_rata_die(d.toordinal()) == t
        assert weekday(*t) == d.weekday()
        assert iso_week_date(*t) == tuple(d.isocalendar())
        assert day_of_year(*t) == d.timetuple().tm_yday
    for a, b in zip(pts, pts[1:]):
        assert days_between(*a, *b) == (D(*b) - D(*a)).days


def test_all_rata_days_sample_and_ends():
    rng = random.Random(9)
    for n in [1, 2, 365, 366, 730119, 730120, 3652058, 3652059] + [rng.randint(1, 3652059) for _ in range(4000)]:
        d = D.fromordinal(n)
        assert date_from_rata_die(n) == (d.year, d.month, d.day)


def test_leap_and_months_all_years():
    for y in range(1, 10000):
        assert is_leap_year(y) == ((D(y, 3, 1) - D(y, 2, 28)).days == 2)
        for mo in range(1, 12):
            assert days_in_month(y, mo) == (D(y, mo + 1, 1) - D(y, mo, 1)).days
        assert days_in_month(y, 12) == 31
        assert (D(y, 12, 31) - D(y, 1, 1)).days + 1 == (366 if is_leap_year(y) else 365)


def oudin(y):
    """Oracle: Oudin's formulation, different from the module's Meeus/Jones/Butcher steps."""
    g = y % 19
    c = y // 100
    h = (c - c // 4 - (8 * c + 13) // 25 + 19 * g + 15) % 30
    i = h - (h // 28) * (1 - (h // 28) * (29 // (h + 1)) * ((21 - g) // 11))
    j = (y + y // 4 + i + 2 - c + c // 4) % 7
    l = i - j
    month = 3 + (l + 40) // 44
    return (month, l + 28 - 31 * (month // 4))


def test_easter_all_years():
    for y in range(1, 10000):
        assert easter_sunday(y) == oudin(y)
        assert D(y, *easter_sunday(y)).weekday() == 6
        assert D(y, 3, 22) <= D(y, *easter_sunday(y)) <= D(y, 4, 25)
    known = {1818: (3, 22), 1943: (4, 25), 2000: (4, 23), 2019: (4, 21), 2024: (3, 31), 2038: (4, 25)}
    for y, v in known.items():
        assert easter_sunday(y) == v
    try:
        from dateutil.easter import easter
    except ImportError:
        return
    for y in range(1, 10000):
        e = easter(y, 3)
        assert easter_sunday(y) == (e.month, e.day)


def test_days_between_extremes():
    assert days_between(1, 1, 1, 9999, 12, 31) == 3652058
    assert days_between(9999, 12, 31, 1, 1, 1) == -3652058
    assert days_between(2024, 5, 5, 2024, 5, 5) == 0


YF = [is_leap_year, lambda y: days_in_month(y, 1), lambda y: date_from_day_of_year(y, 1), easter_sunday,
      lambda y: day_of_year(y, 1, 1), lambda y: rata_die(y, 1, 1), lambda y: weekday(y, 1, 1),
      lambda y: iso_week_date(y, 1, 1)]


@pytest.mark.parametrize('f', YF)
def test_year_refusals(f):
    raises(TypeError, 'y must not be a bool', f, True)
    raises(TypeError, 'y must be an int', f, 2000.0)
    raises(TypeError, 'y must be an int', f, '2000')
    raises(TypeError, 'y must be an int', f, float('nan'))

    class I(int):
        pass
    raises(TypeError, 'y must be an int', f, I(2000))
    for bad in (0, -1, 10000, 10 ** 40, -10 ** 40):
        raises(ValueError, 'y must be between 1 and 9999', f, bad)
    f(1)
    f(9999)


def test_month_day_refusals():
    raises(TypeError, 'm must not be a bool', day_of_year, 2000, True, 1)
    raises(TypeError, 'm must be an int', day_of_year, 2000, 1.0, 1)
    raises(ValueError, 'm must be between 1 and 12', day_of_year, 2000, 0, 1)
    raises(ValueError, 'm must be between 1 and 12', day_of_year, 2000, 13, 1)
    raises(TypeError, 'd must not be a bool', day_of_year, 2000, 1, True)
    raises(TypeError, 'd must be an int', day_of_year, 2000, 1, '1')
    raises(ValueError, 'd must be between 1 and 31', day_of_year, 2000, 1, 0)
    raises(ValueError, 'd must be between 1 and 31', day_of_year, 2000, 1, 32)
    raises(ValueError, 'day does not exist in that month', day_of_year, 2000, 4, 31)
    raises(ValueError, 'day does not exist in that month', day_of_year, 1900, 2, 29)
    raises(ValueError, 'day does not exist in that month', day_of_year, 2001, 2, 29)
    assert day_of_year(2000, 2, 29) == 60 and day_of_year(2000, 1, 31) == 31
    # both bad: y before m before d, range before month-length
    raises(ValueError, 'y must be between 1 and 9999', day_of_year, 0, 13, 40)
    raises(ValueError, 'm must be between 1 and 12', day_of_year, 2000, 13, 40)
    raises(ValueError, 'd must be between 1 and 31', day_of_year, 2000, 2, 40)
    raises(TypeError, 'm must be an int', day_of_year, 2000, 'x', True)
    raises(TypeError, 'y must be an int', day_of_year, 'x', True, True)
    raises(ValueError, 'm must be between 1 and 12', days_in_month, 2000, 0)
    raises(ValueError, 'm must be between 1 and 12', days_in_month, 2000, 13)
    raises(TypeError, 'm must not be a bool', days_in_month, 2000, True)
    raises(TypeError, 'm must be an int', days_in_month, 2000, 1.0)
    raises(ValueError, 'y must be between 1 and 9999', days_in_month, 0, 'x')
    for f in (rata_die, weekday, iso_week_date):
        raises(ValueError, 'day does not exist in that month', f, 2001, 2, 29)
        raises(TypeError, 'd must not be a bool', f, 2001, 2, True)


def test_day_of_year_inverse_refusals():
    raises(ValueError, 'n must be between 1 and the number of days in the year', date_from_day_of_year, 2023, 366)
    raises(ValueError, 'n must be between 1 and the number of days in the year', date_from_day_of_year, 2024, 367)
    raises(ValueError, 'n must be between 1 and the number of days in the year', date_from_day_of_year, 2024, 0)
    assert date_from_day_of_year(2024, 366) == (2024, 12, 31)
    assert date_from_day_of_year(2023, 365) == (2023, 12, 31)
    raises(TypeError, 'n must not be a bool', date_from_day_of_year, 2024, True)
    raises(TypeError, 'n must be an int', date_from_day_of_year, 2024, 1.0)
    raises(ValueError, 'y must be between 1 and 9999', date_from_day_of_year, 0, 'x')


def test_rata_refusals():
    raises(ValueError, 'n must be between 1 and 3652059', date_from_rata_die, 0)
    raises(ValueError, 'n must be between 1 and 3652059', date_from_rata_die, 3652060)
    raises(ValueError, 'n must be between 1 and 3652059', date_from_rata_die, 10 ** 60)
    raises(TypeError, 'n must not be a bool', date_from_rata_die, True)
    raises(TypeError, 'n must be an int', date_from_rata_die, 1.0)
    raises(TypeError, 'n must be an int', date_from_rata_die, float('inf'))


def test_days_between_refusals():
    raises(ValueError, 'y1 must be between 1 and 9999', days_between, 0, 1, 1, 0, 1, 1)
    raises(ValueError, 'y2 must be between 1 and 9999', days_between, 2000, 1, 1, 0, 1, 1)
    raises(TypeError, 'm1 must be an int', days_between, 2000, 1.0, 1, 'x', 1, 1)
    raises(ValueError, 'm2 must be between 1 and 12', days_between, 2000, 1, 1, 2000, 13, 1)
    raises(ValueError, 'd1 must be between 1 and 31', days_between, 2000, 1, 0, 2000, 13, 1)
    raises(ValueError, 'day does not exist in that month', days_between, 2001, 2, 29, 2000, 13, 1)
    raises(TypeError, 'd2 must not be a bool', days_between, 2000, 1, 1, 2000, 1, True)
    raises(ValueError, 'day does not exist in that month', days_between, 2000, 1, 1, 2001, 2, 29)


def test_month_range_before_day_type():
    raises(ValueError, 'm must be between 1 and 12', day_of_year, 2000, 13, 'x')
    raises(ValueError, 'm must be between 1 and 12', day_of_year, 2000, 0, True)
    raises(ValueError, 'y must be between 1 and 9999', day_of_year, 0, 'x', 'x')


def test_era_ends():
    assert date_from_rata_die(146097) == (400, 12, 31)
    for k in range(1, 25):
        n = 146097 * k
        assert date_from_rata_die(n) == (400 * k, 12, 31)
        assert D.fromordinal(n) == D(400 * k, 12, 31)
        assert date_from_rata_die(n + 1) == (400 * k + 1, 1, 1) if 400 * k < 9999 else True
        assert rata_die(400 * k, 12, 31) == n

import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import cron_jobs as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


def _load(src):
    m = types.ModuleType('mutant')
    exec(compile(src, 'mutant', 'exec'), m.__dict__)
    return m


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')  # a syntax error is not a kill
    def _timeout(*_):
        raise TimeoutError('mutant did not terminate')
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return True


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


D = datetime.datetime


def _atoms(field, lo, hi):
    vals = set()
    for part in field.split(','):
        step = 1
        if '/' in part:
            part, s = part.split('/')
            step = int(s)
        if part == '*':
            a, b = lo, hi
        elif '-' in part:
            a, b = (int(x) for x in part.split('-'))
        else:
            a = b = int(part)
        vals |= {v for v in range(a, b + 1) if (v - a) % step == 0}
    return vals


def _oracle(expr, start, count):
    f = expr.split()
    mi, ho, dm, mo, dw = (_atoms(x, lo, hi) for x, (lo, hi) in zip(f, ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))))
    t = start.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    out = []
    while len(out) < count and t < start + datetime.timedelta(days=10):
        wd = t.isoweekday() % 7
        if f[2][0] == '*' or f[4][0] == '*':
            day_ok = t.day in dm and wd in dw
        else:
            day_ok = t.day in dm or wd in dw
        if t.minute in mi and t.hour in ho and t.month in mo and day_ok:
            out.append(t)
        t += datetime.timedelta(minutes=1)
    return out, start + datetime.timedelta(days=10)


def _core(m):
    s = D(2026, 10, 14, 10, 15, 42)
    assert m.next_runs('*/20 * * * *', s, 3) == {'runs': [D(2026, 10, 14, 10, 20), D(2026, 10, 14, 10, 40), D(2026, 10, 14, 11, 0)], 'exhausted': False}
    assert m.next_runs('15 10 * * *', s, 1)['runs'] == [D(2026, 10, 15, 10, 15)]
    assert m.next_runs('16 10 * * *', s, 1)['runs'] == [D(2026, 10, 14, 10, 16)]
    assert m.next_runs('0 9 15 * 1', D(2026, 10, 1, 0, 0), 3)['runs'] == [D(2026, 10, 5, 9, 0), D(2026, 10, 12, 9, 0), D(2026, 10, 15, 9, 0)]
    assert m.next_runs('0 9 15 * *', D(2026, 10, 1, 0, 0), 1)['runs'] == [D(2026, 10, 15, 9, 0)]
    assert m.next_runs('0 9 * * 0', D(2026, 10, 14), 1)['runs'] == [D(2026, 10, 18, 9, 0)]
    assert m.next_runs('30 8 1,15 1-3 *', D(2026, 12, 31), 3)['runs'] == [D(2027, 1, 1, 8, 30), D(2027, 1, 15, 8, 30), D(2027, 2, 1, 8, 30)]
    assert m.next_runs('0 0 29 2 *', D(2026, 1, 1), 1)['runs'] == [D(2028, 2, 29, 0, 0)]
    assert m.next_runs('0 0 31 2 *', D(2026, 1, 1), 2) == {'runs': [], 'exhausted': True}
    assert m.next_runs('0 0 29 2 *', D(2026, 1, 1), 5) == {'runs': [D(2028, 2, 29)], 'exhausted': True}
    for expr in ('* * * * *', '5,35 */6 * * *', '10-20 3 * * 1-5', '0 12 13 * 5', '0 0 */7 * *', '0 9 */2 * 1', '0 9 5 * */2'):
        for st in (s, D(2024, 2, 28, 23, 30)):
            want, end = _oracle(expr, st, 4)
            got = m.next_runs(expr, st, 4)['runs']
            if len(want) == 4:
                assert got == want, (expr, st)
            else:
                assert [g for g in got if g < end] == want, (expr, st)
    assert m.next_runs('0 9 */2 * 1', D(2026, 10, 1), 2)['runs'] == [D(2026, 10, 5, 9, 0), D(2026, 10, 19, 9, 0)]
    assert m.next_runs('0 9 5 * */2', D(2026, 10, 1), 1)['runs'] == [D(2026, 11, 5, 9, 0)]
    assert m.next_runs('0 0 29 2 *', D(2024, 3, 1), 1)['runs'] == [D(2028, 2, 29, 0, 0)]
    assert m.next_runs('5-5 11 * * *', s, 1)['runs'] == [D(2026, 10, 14, 11, 5)]
    assert m.next_runs('10-12 11 * * *', s, 3)['runs'] == [D(2026, 10, 14, 11, 10), D(2026, 10, 14, 11, 11), D(2026, 10, 14, 11, 12)]
    assert len(m.next_runs('* * * * *', s, 20)['runs']) == 20
    _raises(TypeError, 'expression must be a string', m.next_runs, 5, s, 1)
    _raises(ValueError, 'expression must be at most 64 characters', m.next_runs, '*' * 65, s, 1)
    for bad in ('* * * *', '* * * * * *', '', '*  * * * *'):
        _raises(ValueError, 'expression must have five fields', m.next_runs, bad, s, 1)
    for bad in ('60 * * * *', '* 24 * * *', '* * 0 * *', '* * 32 * *', '* * * 0 *', '* * * 13 *', '* * * * 7', 'a * * * *',
                '5-3 * * * *', '*/0 * * * *', '*/61 * * * *', '1,,2 * * * *', '-1 * * * *', '1- * * * *', '001 * * * *', '٣ * * * *'):
        _raises(ValueError, 'invalid cron field', m.next_runs, bad, s, 1)
    assert m.next_runs('*/60 * * * *', s, 2)['runs'] == [D(2026, 10, 14, 11, 0), D(2026, 10, 14, 12, 0)]
    assert m.next_runs('*/59 * * * *', s, 2)['runs'] == [D(2026, 10, 14, 10, 59), D(2026, 10, 14, 11, 0)]
    _raises(TypeError, 'start must be a datetime', m.next_runs, '* * * * *', '2026', 1)
    _raises(TypeError, 'start must be a datetime', m.next_runs, '* * * * *', datetime.date(2026, 1, 1), 1)
    _raises(ValueError, 'start must be naive', m.next_runs, '* * * * *', D(2026, 1, 1, tzinfo=datetime.timezone.utc), 1)
    for y in (1999, 2100):
        _raises(ValueError, 'start year must be between 2000 and 2099', m.next_runs, '* * * * *', D(y, 1, 1), 1)
    for bad in (0, 21, True, 1.0):
        _raises(ValueError, 'count must be a nonbool integer between 1 and 20', m.next_runs, '* * * * *', s, bad)
    assert m.next_runs('* * * * *', D(2000, 1, 1), 1)['runs'] and m.next_runs('* * * * *', D(2099, 1, 1), 1)['runs']
    _raises(ValueError, 'expression must be at most 64 characters', m.next_runs, '*' * 65, 'zzz', 0)



class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class Dc(dict):
    pass


class S(str):
    pass


def _late(m):
    e64 = '10' + ',5' * 27 + ' * * * *'
    assert len(e64) == 64
    assert m.next_runs(e64, D(2026, 1, 1), 1)['runs'] == [D(2026, 1, 1, 0, 5)]
    _raises(ValueError, 'expression must be at most 64 characters', m.next_runs, e64 + ' ', D(2026, 1, 1), 1)
    assert m.next_runs('0 0 */29 2 3', D(2013, 1, 31), 1) == {'runs': [], 'exhausted': True}
    assert m.next_runs('0 0 */29 2 3', D(2013, 2, 1), 1) == {'runs': [D(2017, 2, 1)], 'exhausted': False}
    assert m.next_runs('*/1 * * * *', D(2026, 1, 1), 2)['runs'] == [D(2026, 1, 1, 0, 1), D(2026, 1, 1, 0, 2)]
    for expr in ('* * */31 * *', '* * * */12 *'):
        assert m.next_runs(expr, D(2026, 1, 1), 1)['runs']
    for expr in ('* * */32 * *', '* * */33 * *', '* * * */13 *', '* * * */14 *'):
        _raises(ValueError, 'invalid cron field', m.next_runs, expr, D(2026, 1, 1), 1)
    assert m.next_runs('10-12 11 * * *', D(2026, 10, 14, 10, 0), 4)['runs'] == [
        D(2026, 10, 14, 11, 10), D(2026, 10, 14, 11, 11), D(2026, 10, 14, 11, 12), D(2026, 10, 15, 11, 10)]
    _raises(TypeError, 'expression must be a string', m.next_runs, S('* * * * *'), D(2026, 1, 1), 1)
    class DT(datetime.datetime):
        pass
    _raises(TypeError, 'start must be a datetime', m.next_runs, '* * * * *', DT(2026, 1, 1), 1)
    _raises(ValueError, 'count must be a nonbool integer between 1 and 20', m.next_runs, '* * * * *', D(2026, 1, 1), I(2))


def _sym(m):
    for K in (S,):
        _raises(TypeError, 'expression must be a string', m.next_runs, K('* * * * *'), __import__('datetime').datetime(2024, 1, 1), 1)


def battery(m):
    _core(m)
    _late(m)
    _sym(m)

MUTANTS = [
    ('range(1462)', 'range(1463)'), ('len(expression) > 64', 'len(expression) >= 64'),
    ('_num(part[2:], 1, hi - lo + 1)', '_num(part[2:], 1, hi + lo + 1)'), ('_num(part[2:], 1, hi - lo + 1)', '_num(part[2:], 2, hi - lo + 1)'),
    ('type(expression) is not str', 'not isinstance(expression, str)'),
    ('type(start) is not datetime.datetime', 'not isinstance(start, datetime.datetime)'),
    ('cand > floor', 'cand >= floor'), ('(day.weekday() + 1) % 7', 'day.weekday()'),
    ('(by_dom and by_dow) if (dom_star or dow_star) else (by_dom or by_dow)', '(by_dom or by_dow)'),
    ('(by_dom and by_dow) if (dom_star or dow_star) else (by_dom or by_dow)', '(by_dom and by_dow)'),
    ('(by_dom and by_dow) if (dom_star or dow_star) else (by_dom or by_dow)', '(by_dom and by_dow) if (dom_star and dow_star) else (by_dom or by_dow)'),
    ("parts[2].startswith('*')", "parts[2] == '*'"), ("parts[4].startswith('*')", "parts[4] == '*'"),
    ('if day.month not in month:', 'if False:'), ('range(1462)', 'range(1000)'), ('range(1462)', 'range(1)'),
    ('_num(part[2:], 1, hi - lo + 1)', '_num(part[2:], 0, hi - lo + 1)'), ('_num(part[2:], 1, hi - lo + 1)', '_num(part[2:], 1, hi - lo)'),
    ('range(lo, hi + 1, step)', 'range(0, hi + 1, step)'), ('if a > b:', 'if a >= b:'), ('out.update(range(a, b + 1))', 'out.update(range(a, b))'),
    ('s.isascii() and ', ''), ('len(s) <= 2', 'len(s) <= 3'), ('not lo <= int(s) <= hi', 'not lo <= int(s) < hi'),
    ('LIMITS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))', 'LIMITS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7))'),
    ('LIMITS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))', 'LIMITS = ((1, 59), (0, 23), (1, 31), (1, 12), (0, 6))'),
    ('len(expression) > 64', 'len(expression) > 65'), ('len(parts) != 5', 'len(parts) != 6'),
    ('start.tzinfo is not None', 'False'), ('2000 <= start.year <= 2099', '2000 <= start.year <= 2100'),
    ('2000 <= start.year <= 2099', '2001 <= start.year <= 2099'), ('1 <= count <= 20', '1 <= count <= 21'), ('1 <= count <= 20', '0 <= count <= 20'),
    ('type(count) is not int', 'isinstance(count, bool) or not isinstance(count, int)'), ('type(start) is not datetime.datetime', 'False'),
    ("'exhausted': True}", "'exhausted': False}"), ('if len(runs) == count:', 'if len(runs) == count + 1:'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)

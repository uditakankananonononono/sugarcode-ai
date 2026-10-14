import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import incident_timeline as mod

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


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __ne__(self, o): return False
    def __eq__(self, o): return True
    __hash__ = int.__hash__


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('web')


ORDER = ['open', 'ack', 'mitigate', 'resolve']


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: stage timing of supplied incident events, no paging or tickets'
    assert len(mod.NOT_CLAIMED) >= 4 and 'paging people' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ev, br):
    """Independent: dict lookups by stage name."""
    at = {s: t for t, s in ev}
    t0 = at['open']
    end = max(t for t, _ in ev)
    return {'state': [s for t, s in ev][-1],
            'durations': {'ack': at['ack'] - t0 if 'ack' in at else None,
                          'mitigate': at['mitigate'] - t0 if 'mitigate' in at else None,
                          'resolve': at['resolve'] - t0 if 'resolve' in at else None},
            'resolved': 'resolve' in at, 'elapsed': end - t0, 'breached': end - t0 > br}


def _core(m):
    full = [(10, 'open'), (15, 'ack'), (40, 'mitigate'), (70, 'resolve')]
    assert m.incident_timeline(full) == {'state': 'resolve', 'durations': {'ack': 5, 'mitigate': 30, 'resolve': 60},
                                         'resolved': True, 'elapsed': 60, 'breached': False}
    assert m.incident_timeline(full, 59)['breached'] is True
    assert m.incident_timeline(full, 60)['breached'] is False
    assert m.incident_timeline([(0, 'open')]) == {'state': 'open', 'durations': {'ack': None, 'mitigate': None, 'resolve': None},
                                                  'resolved': False, 'elapsed': 0, 'breached': False}
    assert m.incident_timeline([(0, 'open'), (61, 'ack')]) == {'state': 'ack', 'durations': {'ack': 61, 'mitigate': None, 'resolve': None},
                                                               'resolved': False, 'elapsed': 61, 'breached': True}
    assert m.incident_timeline([(0, 'open'), (60, 'ack')])['breached'] is False
    assert m.incident_timeline([(5, 'open'), (5, 'resolve')]) == {'state': 'resolve', 'durations': {'ack': None, 'mitigate': None, 'resolve': 0},
                                                                  'resolved': True, 'elapsed': 0, 'breached': False}
    assert m.incident_timeline([[3, 'open'], (3, 'ack'), (4, 'mitigate')])['durations'] == {'ack': 0, 'mitigate': 1, 'resolve': None}
    assert m.incident_timeline(tuple(full)) == m.incident_timeline(full)
    assert m.incident_timeline([(100000, 'open')])['elapsed'] == 0
    assert m.incident_timeline([(0, 'open'), (100000, 'resolve')], 100000)['breached'] is False
    assert m.incident_timeline([(0, 'open'), (100000, 'resolve')], 99999)['breached'] is True
    assert m.incident_timeline([(0, 'open'), (100, 'ack')])['breached'] is True      # default 60, not 120 or 100
    assert m.incident_timeline([(0, 'open'), (61, 'ack')], 1)['breached'] is True and m.incident_timeline([(0, 'open'), (1, 'ack')], 1)['breached'] is False
    rng = random.Random(637)
    for _ in range(600):
        stages = [s for s in ORDER[1:] if rng.random() < .6]
        names = ['open'] + stages
        t, ev = rng.randint(0, 50), []
        for s in names:
            ev.append((t, s))
            t += rng.choice([0, 1, rng.randint(0, 90)])
        br = rng.choice([1, 30, 60, 61, rng.randint(1, 200)])
        assert m.incident_timeline(ev, br) == _oracle(ev, br), (ev, br)


def _late(m):
    EV = 'events must be a list or tuple'
    SZ = 'events must contain 1 to 4 entries'
    BR = 'breach_minutes must be a nonbool integer between 1 and 100000'
    PR = 'each event must be a (minute, stage) pair'
    MN = 'minute must be a nonbool integer between 0 and 100000'
    ST = 'stage must be open, ack, mitigate or resolve'
    FO = 'the first event must be open'
    AD = 'stages must advance'
    DE = 'minutes must not decrease'
    ok = (0, 'open')
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, EV, m.incident_timeline, bad)
    _raises(TypeError, EV, m.incident_timeline, L([ok] * 5))
    _raises(ValueError, SZ, m.incident_timeline, [])
    _raises(ValueError, SZ, m.incident_timeline, [ok] * 5)
    assert len(m.incident_timeline([ok])['durations']) == 3
    assert m.incident_timeline([ok, (1, 'ack'), (2, 'mitigate'), (3, 'resolve')])['elapsed'] == 3
    _raises(ValueError, SZ, m.incident_timeline, [ok, (1, 'ack'), (2, 'mitigate'), (3, 'resolve'), (4, 'resolve')])
    for bad in (0, 100001, -1, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, BR, m.incident_timeline, [ok], bad)
    assert m.incident_timeline([ok], 1) and m.incident_timeline([ok], 100000)
    for K in (L, T):
        for bad in (K(ok), K((1,))):
            _raises(ValueError, PR, m.incident_timeline, [bad])
            _raises(ValueError, PR, m.incident_timeline, [ok, bad])
    for bad in ('ab', None, 5, (1,), (1, 'open', 1), ()):
        _raises(ValueError, PR, m.incident_timeline, [bad])
        _raises(ValueError, PR, m.incident_timeline, [ok, bad])
    for bad in (-1, 100001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MN, m.incident_timeline, [(bad, 'open')])
        _raises(ValueError, MN, m.incident_timeline, [ok, (bad, 'ack')])
    for bad in ('', 'OPEN', 'closed', None, 5, S('ack'), LyingS('ack'), b'ack', ['ack']):
        _raises(ValueError, ST, m.incident_timeline, [(0, bad)])
        _raises(ValueError, ST, m.incident_timeline, [ok, (0, bad)])
    _raises(ValueError, FO, m.incident_timeline, [(0, 'ack')])
    _raises(ValueError, FO, m.incident_timeline, [(0, 'resolve')])
    for pair in (('open', 'open'), ('ack', 'ack'), ('mitigate', 'ack'), ('resolve', 'mitigate'), ('resolve', 'open')):
        seq = [ok]
        if pair[0] != 'open':
            seq.append((0, pair[0]))
        seq.append((0, pair[1]))
        _raises(ValueError, AD, m.incident_timeline, seq)
    _raises(ValueError, DE, m.incident_timeline, [(5, 'open'), (4, 'ack')])
    _raises(ValueError, DE, m.incident_timeline, [(5, 'open'), (5, 'ack'), (4, 'mitigate')])
    assert m.incident_timeline([(5, 'open'), (5, 'ack')])['elapsed'] == 0
    # order: events type, size, breach, then per event: shape, minute, stage, first-open, advance, decrease
    _raises(TypeError, EV, m.incident_timeline, L([1]), I(1))
    _raises(ValueError, SZ, m.incident_timeline, [], I(1))
    _raises(ValueError, BR, m.incident_timeline, [1], I(1))
    _raises(ValueError, PR, m.incident_timeline, [1], 5)
    _raises(ValueError, MN, m.incident_timeline, [(I(1), 'zzz')])
    _raises(ValueError, ST, m.incident_timeline, [(0, 'zzz')])
    _raises(ValueError, FO, m.incident_timeline, [(0, 'ack')])
    _raises(ValueError, FO, m.incident_timeline, [(9, 'ack')])
    _raises(ValueError, AD, m.incident_timeline, [ok, (0, 'ack'), (0, 'ack')])
    _raises(ValueError, AD, m.incident_timeline, [(5, 'open'), (4, 'open')])               # advance before decrease
    _raises(ValueError, MN, m.incident_timeline, [ok, (100001, 'open')])                   # minute before advance
    _raises(ValueError, ST, m.incident_timeline, [ok, (5, 'zzz'), (-1, 'zzz')])


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('ack')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(events) not in (list, tuple)", "not isinstance(events, (list, tuple))"),
    ("not 1 <= len(events) <= MAX_EVENTS", "not 0 <= len(events) <= MAX_EVENTS"),
    ("not 1 <= len(events) <= MAX_EVENTS", "not 1 <= len(events) < MAX_EVENTS"),
    ("MAX_EVENTS = 4", "MAX_EVENTS = 5"),
    ("MAX_MINUTE = 100000", "MAX_MINUTE = 99999"),
    ("MAX_MINUTE = 100000", "MAX_MINUTE = 100001"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(breach_minutes, 1, MAX_MINUTE", "_int(breach_minutes, 0, MAX_MINUTE"),
    ("breach_minutes=60", "breach_minutes=61"),
    ("breach_minutes=60", "breach_minutes=59"),
    ("type(e) not in (list, tuple) or len(e) != 2", "not isinstance(e, (list, tuple)) or len(e) != 2"),
    ("or len(e) != 2", "or len(e) > 2"),
    ("or len(e) != 2", "or len(e) < 2"),
    ("_int(minute, 0, MAX_MINUTE", "_int(minute, 1, MAX_MINUTE"),
    ("type(stage) is not str or stage not in STAGES", "not isinstance(stage, str) or stage not in STAGES"),
    ("STAGES = ('open', 'ack', 'mitigate', 'resolve')", "STAGES = ('open', 'ack', 'resolve', 'mitigate')"),
    ("if last_stage == -1 and idx != 0:", "if last_stage == -1 and idx != 1:"),
    ("if last_stage == -1 and idx != 0:", "if False:"),
    ("if idx <= last_stage:", "if idx < last_stage:"),
    ("if idx <= last_stage:", "if False:"),
    ("if minute < last_minute:", "if minute <= last_minute:"),
    ("if minute < last_minute:", "if False:"),
    ("seen[stage] = minute", "seen[stage] = minute + 1"),
    ("elapsed = last_minute - start", "elapsed = last_minute"),
    ("'breached': elapsed > breach_minutes", "'breached': elapsed >= breach_minutes"),
    ("(seen[s] - start if s in seen else None)", "(seen[s] if s in seen else None)"),
    ("'resolved': 'resolve' in seen", "'resolved': last_stage >= 2"),
    ("'state': STAGES[last_stage]", "'state': STAGES[0]"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

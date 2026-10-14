import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import mentalizing as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


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
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: state sequence summarizing over supplied events, no real mentalizing'
    assert len(mod.NOT_CLAIMED) >= 4 and 'prediction' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_EVENTS, mod.STATES) == (100, ('calm', 'curious', 'anxious', 'focused'))


def _oracle(events):
    """Independent: counts via list .count, shifts with a zip walk."""
    shifts = 0
    for earlier, later in zip(events, events[1:]):
        if earlier != later:
            shifts += 1
    return {'calm': events.count('calm'), 'curious': events.count('curious'),
            'anxious': events.count('anxious'), 'focused': events.count('focused'),
            'final': events[-1] if len(events) > 0 else None, 'shifts': shifts}


def _core(m):
    assert m.track(['calm', 'calm', 'anxious', 'focused', 'anxious']) == {
        'calm': 2, 'curious': 0, 'anxious': 2, 'focused': 1,
        'final': 'anxious', 'shifts': 3}
    assert m.track([]) == {'calm': 0, 'curious': 0, 'anxious': 0, 'focused': 0,
                           'final': None, 'shifts': 0}
    # one event is no shift
    assert m.track(['curious'])['shifts'] == 0
    # an unbroken run never shifts
    assert m.track(['calm', 'calm', 'calm'])['shifts'] == 0
    # every alternation shifts
    assert m.track(['calm', 'anxious', 'calm'])['shifts'] == 2
    # returning to an earlier state still shifts
    assert m.track(['focused', 'calm', 'focused']) == {
        'calm': 1, 'curious': 0, 'anxious': 0, 'focused': 2,
        'final': 'focused', 'shifts': 2}
    # the final state is the last event, not the most frequent
    assert m.track(['anxious', 'anxious', 'calm'])['final'] == 'calm'
    # tuples accepted
    assert m.track(('calm',))['final'] == 'calm'
    rng = random.Random(763)
    for _ in range(400):
        events = [rng.choice(['calm', 'curious', 'anxious', 'focused'])
                  for _ in range(rng.randint(0, 12))]
        assert m.track(events) == _oracle(events)


def _late(m):
    EVT = 'events must be a list or tuple'
    CAP = 'events must contain at most 100 rows'
    STT = 'events must be calm, curious, anxious, or focused'
    good = ['calm']
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, EVT, m.track, bad)
    _raises(TypeError, EVT, m.track, L(good * 101))             # subclass refused before the cap
    _raises(ValueError, CAP, m.track, good * 101)
    assert m.track(good * 100)['calm'] == 100
    for bad in ('', 'CALM', 'calm ', 'happy', None, 5, b'calm',
                S('calm'), LyingS('calm'), I(0), ('calm',)):
        _raises(ValueError, STT, m.track, [bad])
        _raises(ValueError, STT, m.track, ['calm', bad])
    # order: container, cap, events; the first bad event reports first
    _raises(TypeError, EVT, m.track, L(good))
    _raises(ValueError, CAP, m.track, [5] * 101)
    _raises(ValueError, STT, m.track, [S('calm')])
    _raises(ValueError, STT, m.track, [5, 'x' * 61])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    events = ['calm', 'anxious']
    assert mod.track(events)['shifts'] == 1
    assert events == ['calm', 'anxious']
    assert mod.track(events)['final'] == 'anxious'


MUTANTS = [
    ("    if type(events) not in (list, tuple):", "    if not isinstance(events, (list, tuple)):"),
    ("    if len(events) > MAX_EVENTS:", "    if len(events) >= MAX_EVENTS:"),
    ("MAX_EVENTS = 100", "MAX_EVENTS = 101"),
    ("        if type(event) is not str or event not in STATES:",
     "        if not isinstance(event, str) or event not in STATES:"),
    ("event not in STATES", "event not in STATES[:3]"),
    ("STATES = ('calm', 'curious', 'anxious', 'focused')", "STATES = ('calm', 'curious', 'anxious')"),
    ("    counts = {'calm': 0, 'curious': 0, 'anxious': 0, 'focused': 0}",
     "    counts = {'calm': 1, 'curious': 0, 'anxious': 0, 'focused': 0}"),
    ("        counts[event] += 1", "        counts[event] += 2"),
    ("        counts[event] += 1", "        counts['calm'] += 1"),
    ("    shifts = 0", "    shifts = 1"),
    ("    for index in range(1, len(events)):", "    for index in range(0, len(events)):"),
    ("    for index in range(1, len(events)):", "    for index in range(1, len(events) - 1):"),
    ("        if events[index] != events[index - 1]:", "        if events[index] != events[0]:"),
    ("        if events[index] != events[index - 1]:", "        if events[index] == events[index - 1]:"),
    ("            shifts += 1", "            shifts += 2"),
    ("            'final': events[-1] if events else None, 'shifts': shifts}",
     "            'final': events[0] if events else None, 'shifts': shifts}"),
    ("            'final': events[-1] if events else None, 'shifts': shifts}",
     "            'final': None, 'shifts': shifts}"),
    ("            'final': events[-1] if events else None, 'shifts': shifts}",
     "            'final': events[-1] if events else 'calm', 'shifts': shifts}"),
    ("    for event in events:\n        counts[event] += 1",
     "    for event in events[1:]:\n        counts[event] += 1"),
    ("'events must be a list or tuple'", "'events must be a sequence'"),
    ("'events must contain at most 100 rows'", "'events must contain at most 99 rows'"),
    ("'events must be calm, curious, anxious, or focused'",
     "'events must be calm, curious, or anxious'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

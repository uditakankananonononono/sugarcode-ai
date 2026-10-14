import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import empathy as mod

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
    assert mod.SCOPE == 'PARTIAL: signal matching over supplied rows, no real empathy'
    assert len(mod.NOT_CLAIMED) >= 4 and 'counseling' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_PERSON, mod.EMOTIONS) == (100, 8, ('joy', 'sadness', 'anger', 'fear'))


def _oracle(rows):
    """Independent: counts via a flat loop, mirrored with a zip walk."""
    joy = sadness = anger = fear = 0
    for person, emotion in rows:
        if emotion == 'joy':
            joy += 1
        elif emotion == 'sadness':
            sadness += 1
        elif emotion == 'anger':
            anger += 1
        else:
            fear += 1
    mirrored = 0
    for earlier, later in zip(rows, rows[1:]):
        if earlier[1] == later[1]:
            mirrored += 1
    return {'joy': joy, 'sadness': sadness, 'anger': anger, 'fear': fear,
            'mirrored': mirrored, 'total': len(rows)}


def _core(m):
    assert m.resonate([('a', 'joy'), ('b', 'joy'), ('c', 'fear'),
                       ('d', 'fear'), ('e', 'fear')]) == {
        'joy': 2, 'sadness': 0, 'anger': 0, 'fear': 3, 'mirrored': 3, 'total': 5}
    assert m.resonate([]) == {'joy': 0, 'sadness': 0, 'anger': 0, 'fear': 0,
                              'mirrored': 0, 'total': 0}
    # alternating emotions never mirror
    assert m.resonate([('a', 'joy'), ('b', 'fear'), ('c', 'joy')])['mirrored'] == 0
    # the same emotion from the same person still mirrors
    assert m.resonate([('a', 'anger'), ('a', 'anger')])['mirrored'] == 1
    # mirroring is about emotion, not person
    assert m.resonate([('a', 'joy'), ('b', 'joy')])['mirrored'] == 1
    assert m.resonate([('a', 'joy'), ('a', 'fear')])['mirrored'] == 0
    # one row is no mirror
    assert m.resonate([('a', 'sadness')])['mirrored'] == 0
    # tuples accepted at every level
    assert m.resonate((('a', 'joy'),))['total'] == 1
    rng = random.Random(764)
    for _ in range(400):
        rows = [(rng.choice(['a', 'b', 'cy']), rng.choice(['joy', 'sadness', 'anger', 'fear']))
                for _ in range(rng.randint(0, 10))]
        assert m.resonate(rows) == _oracle(rows)


def _late(m):
    SIG = 'signals must be a list or tuple'
    CAP = 'signals must contain at most 100 rows'
    ROW = 'each signal must be a (person, emotion) row'
    PER = 'person must be a string of 1 to 8 characters'
    EMO = 'emotion must be joy, sadness, anger, or fear'
    good = [('a', 'joy')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, SIG, m.resonate, bad)
    _raises(TypeError, SIG, m.resonate, L(good * 101))          # subclass refused before the cap
    _raises(ValueError, CAP, m.resonate, good * 101)
    assert m.resonate(good * 100)['total'] == 100
    for bad in ('aj', 5, None, ('a',), ('a', 'joy', 'x'), ()):
        _raises(ValueError, ROW, m.resonate, [bad])
        _raises(ValueError, ROW, m.resonate, [('a', 'joy'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.resonate, [K(('a', 'joy'))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, PER, m.resonate, [(bad, 'joy')])
        _raises(ValueError, PER, m.resonate, [('a', 'joy'), (bad, 'fear')])
    for bad in ('', 'JOY', 'joy ', 'happy', None, 5, S('joy'), LyingS('joy'), I(0)):
        _raises(ValueError, EMO, m.resonate, [('a', bad)])
        _raises(ValueError, EMO, m.resonate, [('a', 'joy'), ('b', bad)])
    assert m.resonate([('x' * 8, 'fear')])['fear'] == 1
    assert m.resonate([('x', 'joy')])['joy'] == 1                # single-character person accepted
    # order: container, cap, rows (shape, person, emotion)
    _raises(TypeError, SIG, m.resonate, L(good))
    _raises(ValueError, CAP, m.resonate, [('a', 'maybe')] * 101)
    _raises(ValueError, ROW, m.resonate, [('a', 'joy', 'x')])
    _raises(ValueError, PER, m.resonate, [(S('a'), 'joy')])
    _raises(ValueError, EMO, m.resonate, [('a', S('joy'))])
    # the first bad row reports first
    _raises(ValueError, PER, m.resonate, [(5, 'maybe'), ('a', 'joy', 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    signals = [('a', 'joy'), ('b', 'joy')]
    assert mod.resonate(signals)['mirrored'] == 1
    assert signals == [('a', 'joy'), ('b', 'joy')]
    assert mod.resonate(signals)['joy'] == 2


MUTANTS = [
    ("    if type(signals) not in (list, tuple):", "    if not isinstance(signals, (list, tuple)):"),
    ("    if len(signals) > MAX_ROWS:", "    if len(signals) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(person) is not str or not 1 <= len(person) <= MAX_PERSON:",
     "        if not isinstance(person, str) or not 1 <= len(person) <= MAX_PERSON:"),
    ("not 1 <= len(person) <= MAX_PERSON", "not 1 <= len(person) < MAX_PERSON"),
    ("MAX_PERSON = 8", "MAX_PERSON = 9"),
    ("        if type(emotion) is not str or emotion not in EMOTIONS:",
     "        if not isinstance(emotion, str) or emotion not in EMOTIONS:"),
    ("emotion not in EMOTIONS", "emotion not in EMOTIONS[:3]"),
    ("EMOTIONS = ('joy', 'sadness', 'anger', 'fear')", "EMOTIONS = ('joy', 'sadness', 'anger')"),
    ("    counts = {'joy': 0, 'sadness': 0, 'anger': 0, 'fear': 0}",
     "    counts = {'joy': 1, 'sadness': 0, 'anger': 0, 'fear': 0}"),
    ("        counts[emotion] += 1", "        counts[emotion] += 2"),
    ("        counts[emotion] += 1", "        counts['joy'] += 1"),
    ("    mirrored = 0", "    mirrored = 1"),
    ("    for index in range(1, len(rows)):", "    for index in range(0, len(rows)):"),
    ("    for index in range(1, len(rows)):", "    for index in range(1, len(rows) - 1):"),
    ("        if rows[index][1] == rows[index - 1][1]:", "        if rows[index][0] == rows[index - 1][0]:"),
    ("        if rows[index][1] == rows[index - 1][1]:", "        if rows[index][1] != rows[index - 1][1]:"),
    ("            mirrored += 1", "            mirrored += 2"),
    ("    for person, emotion in rows:\n        counts[emotion] += 1",
     "    for person, emotion in rows[1:]:\n        counts[emotion] += 1"),
    ("            'mirrored': mirrored, 'total': len(rows)}",
     "            'mirrored': mirrored, 'total': len(rows) + 1}"),
    ("'signals must be a list or tuple'", "'signals must be a sequence'"),
    ("'signals must contain at most 100 rows'", "'signals must contain at most 99 rows'"),
    ("'each signal must be a (person, emotion) row'", "'each signal must be a (person, emotion) tuple'"),
    ("'person must be a string of 1 to 8 characters'", "'person must be a string of 1 to 7 characters'"),
    ("'emotion must be joy, sadness, anger, or fear'", "'emotion must be joy, sadness, or anger'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

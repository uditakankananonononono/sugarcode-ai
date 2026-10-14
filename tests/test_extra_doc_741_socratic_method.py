import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import socratic_method as mod

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
    assert mod.SCOPE == 'PARTIAL: turn-structure audit over supplied turns, no real dialogue'
    assert len(mod.NOT_CLAIMED) >= 4 and 'pedagogy' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_TURNS, mod.MAX_TEXT) == (100, 80)


def _oracle(rows):
    """Independent: walk even indices only, first non-question wins."""
    probes = 0
    stopped_at = None
    for index in range(0, len(rows), 2):
        text = rows[index][1]
        if text.endswith('?'):
            probes += 1
        elif stopped_at is None:
            stopped_at = index
    return {'probes': probes, 'turns': len(rows), 'stopped_at': stopped_at}


def _core(m):
    # every teacher turn probes: stopped_at stays None
    assert m.probe([('teacher', 'Why?'), ('student', 'Because.'),
                    ('teacher', 'What else?')]) == {'probes': 2, 'turns': 3, 'stopped_at': None}
    # the first non-probe teacher turn stops the count
    assert m.probe([('teacher', 'Listen.'), ('student', 'ok'), ('teacher', 'See?')]) == {
        'probes': 1, 'turns': 3, 'stopped_at': 0}
    # a later stop wins over a later probe
    assert m.probe([('teacher', 'Why?'), ('student', 'x'), ('teacher', 'Hmm.'),
                    ('student', 'y'), ('teacher', 'Really?')]) == {
        'probes': 2, 'turns': 5, 'stopped_at': 2}
    assert m.probe([]) == {'probes': 0, 'turns': 0, 'stopped_at': None}
    # student texts never count, even when they end with ?
    assert m.probe([('teacher', 'Why?'), ('student', 'Why not?')])['probes'] == 1
    # a question mark mid-text is not a probe
    assert m.probe([('teacher', 'a? b.')])['probes'] == 0
    # a teacher statement after a probe stops at that statement
    assert m.probe([('teacher', 'a?'), ('student', 'b'), ('teacher', 'c.')])['stopped_at'] == 2
    # tuples accepted at every level
    assert m.probe((('teacher', 'a?'),))['probes'] == 1
    rng = random.Random(741)
    for _ in range(400):
        rows = []
        for i in range(rng.randint(0, 12)):
            speaker = 'teacher' if i % 2 == 0 else 'student'
            text = 't%d%s' % (i, '?' if rng.random() < 0.5 else '.')
            rows.append((speaker, text))
        assert m.probe(rows) == _oracle(rows)


def _late(m):
    TRN = 'turns must be a list or tuple'
    CAP = 'turns must contain at most 100 rows'
    ROW = 'each turn must be a (speaker, text) row'
    SPK = 'speaker must be the string teacher or student'
    TXT = 'text must be a string of 1 to 80 characters'
    ALT = 'turns must alternate starting with the teacher'
    good = [('teacher', 'a?')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, TRN, m.probe, bad)
    _raises(TypeError, TRN, m.probe, L(good * 101))             # subclass refused before the cap
    _raises(ValueError, CAP, m.probe, good * 101)
    assert m.probe([('teacher', 'a?'), ('student', 'b')] * 50)['turns'] == 100
    for K in (L, T):
        for bad in (K(('teacher', 'a?')), K(('teacher',))):
            _raises(ValueError, ROW, m.probe, [bad])
    for bad in ('teacher', 5, None, ('teacher',), ('teacher', 'a?', 'x'), ()):
        _raises(ValueError, ROW, m.probe, [bad])
        _raises(ValueError, ROW, m.probe, [('teacher', 'a?'), bad])
    for bad in ('', 'Teacher', None, 5, b'teacher', S('teacher'), LyingS('teacher')):
        _raises(ValueError, SPK, m.probe, [(bad, 'a?')])
    # a valid student speaker in the teacher's slot breaks alternation instead
    _raises(ValueError, ALT, m.probe, [('student', 'a?')])
    _raises(ValueError, ALT, m.probe, [('teacher', 'a?'), ('teacher', 'b?')])
    _raises(ValueError, ALT, m.probe, [('teacher', 'a?'), ('student', 'b'), ('student', 'c')])
    for bad in ('', 'x' * 81, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, TXT, m.probe, [('teacher', bad)])
        _raises(ValueError, TXT, m.probe, [('teacher', 'a?'), ('student', bad)])
    assert m.probe([('teacher', 'x' * 79 + '?')])['probes'] == 1
    # order: container, cap, rows (shape, speaker, text, alternation)
    _raises(TypeError, TRN, m.probe, L(good))
    _raises(ValueError, CAP, m.probe, [('x', 1, 2)] * 101)
    _raises(ValueError, ROW, m.probe, [('teacher',)])
    _raises(ValueError, SPK, m.probe, [(S('teacher'), 5)])
    _raises(ValueError, TXT, m.probe, [('teacher', S('a'))])
    _raises(ValueError, TXT, m.probe, [('student', S('a'))])
    _raises(ValueError, TXT, m.probe, [('student', S('a'))])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    turns = [('teacher', 'a?'), ('student', 'b')]
    r = mod.probe(turns)
    r['probes'] = 99
    assert turns == [('teacher', 'a?'), ('student', 'b')]
    assert mod.probe(turns)['probes'] == 1


MUTANTS = [
    ("    if type(turns) not in (list, tuple):", "    if not isinstance(turns, (list, tuple)):"),
    ("    if len(turns) > MAX_TURNS:", "    if len(turns) >= MAX_TURNS:"),
    ("MAX_TURNS = 100", "MAX_TURNS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(speaker) is not str or speaker not in ('teacher', 'student'):",
     "        if not isinstance(speaker, str) or speaker not in ('teacher', 'student'):"),
    ("or speaker not in ('teacher', 'student')", "or speaker not in ('teacher',)"),
    ("        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:",
     "        if not isinstance(text, str) or not 1 <= len(text) <= MAX_TEXT:"),
    ("not 1 <= len(text) <= MAX_TEXT", "not 1 <= len(text) < MAX_TEXT"),
    ("MAX_TEXT = 80", "MAX_TEXT = 81"),
    ("        if speaker != ('teacher' if index % 2 == 0 else 'student'):",
     "        if speaker != ('student' if index % 2 == 0 else 'teacher'):"),
    ("        if speaker != ('teacher' if index % 2 == 0 else 'student'):",
     "        if speaker != ('teacher' if index % 2 == 1 else 'student'):"),
    ("        rows.append((speaker, text))", "        rows.append((text, speaker))"),
    ("        if speaker != 'teacher':", "        if speaker == 'teacher':"),
    ("        if text.endswith('?'):", "        if text.startswith('?'):"),
    ("        if text.endswith('?'):", "        if '?' in text:"),
    ("            probes += 1", "            probes += 2"),
    ("        elif stopped_at is None:", "        elif stopped_at is not None:"),
    ("            stopped_at = index", "            stopped_at = index + 1"),
    ("    probes = 0", "    probes = 1"),
    ("    stopped_at = None", "    stopped_at = 0"),
    ("    for index, (speaker, text) in enumerate(rows):",
     "    for index, (speaker, text) in enumerate(rows, 1):"),
    ("    return {'probes': probes, 'turns': len(rows), 'stopped_at': stopped_at}",
     "    return {'probes': probes, 'turns': len(rows) + 1, 'stopped_at': stopped_at}"),
    ("    return {'probes': probes, 'turns': len(rows), 'stopped_at': stopped_at}",
     "    return {'probes': probes, 'turns': probes, 'stopped_at': stopped_at}"),
    ("'turns must be a list or tuple'", "'turns must be a sequence'"),
    ("'turns must contain at most 100 rows'", "'turns must contain at most 99 rows'"),
    ("'each turn must be a (speaker, text) row'", "'each turn must be a (speaker, text) tuple'"),
    ("'speaker must be the string teacher or student'", "'speaker must be the string teacher'"),
    ("'text must be a string of 1 to 80 characters'", "'text must be a string of 1 to 79 characters'"),
    ("'turns must alternate starting with the teacher'",
     "'turns must alternate starting with the student'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

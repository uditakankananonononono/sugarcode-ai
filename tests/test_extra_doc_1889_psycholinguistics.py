import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import psycholinguistics as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SM = 'row 1: subject must be a string of 1 to 16 characters'
TM = 'row 1: stimulus must be a string of 1 to 16 characters'
RM = 'row 1: reaction must be a nonbool integer between 1 and 9'


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
    code = compile(mutated, 'mutant', 'exec')
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


def test_disclaimer_text_exact():
    section = ' '.join(mod.__doc__.split('NOT_CLAIMED:', 1)[1].split())
    assert section == ('lexical access, reaction-time validity, language '
                       'acquisition, the mental lexicon, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: priming measurement over supplied reactions'
    assert mod.NOT_CLAIMED == ('lexical access', 'reaction-time validity',
                               'language acquisition', 'the mental lexicon',
                               'production readiness')


def _expected(rows):
    per_pair = {}
    for subject, stimulus, reaction in rows:
        if subject not in per_pair:
            per_pair[subject] = {}
        if stimulus not in per_pair[subject]:
            per_pair[subject][stimulus] = reaction
        elif reaction > per_pair[subject][stimulus]:
            per_pair[subject][stimulus] = reaction
    peak = {}
    primed = {}
    numb = []
    for subject in per_pair:
        best = None
        hits = []
        for stimulus in per_pair[subject]:
            if best is None or per_pair[subject][stimulus] > best:
                best = per_pair[subject][stimulus]
            if per_pair[subject][stimulus] >= 8:
                hits.append(stimulus)
        peak[subject] = best
        if hits:
            primed[subject] = sorted(hits)
        else:
            numb.append(subject)
    sensitive = None
    for subject in primed:
        if sensitive is None or len(primed[subject]) > len(primed[sensitive]):
            sensitive = subject
    return {'total': len(rows), 'peak': peak, 'primed': primed,
            'numb': sorted(numb), 'sensitive': sensitive}


def _core(m):
    # fixed pins, oracle seeded with row number 1889
    assert m.measure_priming([('s1', 'doctor', 8), ('s1', 'nurse', 3),
                              ('s1', 'nurse', 9), ('s2', 'nurse', 2)]) == {
        'total': 4, 'peak': {'s1': 9, 's2': 2},
        'primed': {'s1': ['doctor', 'nurse']},
        'numb': ['s2'], 'sensitive': 's1'}
    # one soft row: numb subject, no sensitive at all
    assert m.measure_priming([('s', 't', 5)]) == {
        'total': 1, 'peak': {'s': 5}, 'primed': {}, 'numb': ['s'],
        'sensitive': None}
    # a reaction of exactly 8 primes
    r = m.measure_priming([('s', 't', 8)])
    assert r['primed'] == {'s': ['t']} and r['sensitive'] == 's'
    # a reaction of 7 never primes, even in sum
    r = m.measure_priming([('s', 't', 7), ('s', 't', 7)])
    assert r['primed'] == {} and r['numb'] == ['s'] and r['peak'] == {'s': 7}
    # the pair keeps the peak reaction, not the latest
    r = m.measure_priming([('s', 't', 9), ('s', 't', 1)])
    assert r['peak'] == {'s': 9} and r['primed'] == {'s': ['t']}
    # the sensitive tie goes to the first supplied
    r = m.measure_priming([('a', 't', 9), ('b', 'u', 9)])
    assert r['sensitive'] == 'a'
    # most primed stimuli wins over a higher single peak
    r = m.measure_priming([('a', 't', 8), ('a', 'u', 8), ('b', 'v', 9)])
    assert r['sensitive'] == 'a' and r['peak'] == {'a': 8, 'b': 9}
    # dicts keep first-touch order
    r = m.measure_priming([('z', 't', 1), ('a', 'u', 2)])
    assert r['peak'] == {'z': 1, 'a': 2}
    # non-ASCII subjects and stimuli follow the same rule
    r = m.measure_priming([('Üser-9!', 'Ω-1', 9), ('q?7', 'Ω-1', 1)])
    assert r == {'total': 2, 'peak': {'Üser-9!': 9, 'q?7': 1},
                 'primed': {'Üser-9!': ['Ω-1']}, 'numb': ['q?7'],
                 'sensitive': 'Üser-9!'}
    rng = random.Random(1889)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.measure_priming(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.measure_priming, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.measure_priming, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.measure_priming, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.measure_priming, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (subject, stimulus, reaction) triple',
            m.measure_priming, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.measure_priming, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.measure_priming, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SM, m.measure_priming, [(1, 'b', 1)])
    _raises(ValueError, SM, m.measure_priming, [('', 'b', 1)])
    _raises(ValueError, SM, m.measure_priming, [('x' * 17, 'b', 1)])
    _raises(ValueError, TM, m.measure_priming, [('a', 1, 1)])
    _raises(ValueError, TM, m.measure_priming, [('a', '', 1)])
    _raises(ValueError, TM, m.measure_priming, [('a', 'x' * 17, 1)])
    _raises(ValueError, RM, m.measure_priming, [('a', 'b', '1')])
    _raises(ValueError, RM, m.measure_priming, [('a', 'b', 0)])
    _raises(ValueError, RM, m.measure_priming, [('a', 'b', 10)])
    _raises(ValueError, RM, m.measure_priming, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: subject must be a string of 1 to 16 characters',
            m.measure_priming, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: reaction must be a nonbool integer between 1 and 9',
            m.measure_priming, [('a', 'b', 1), ('c', 'd', 0)])
    # subject is validated before stimulus, stimulus before reaction
    _raises(ValueError, SM, m.measure_priming, [('x' * 17, '', 0)])
    _raises(ValueError, TM, m.measure_priming, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.measure_priming, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.measure_priming((('a', 'b', 1),)) == m.measure_priming([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.measure_priming([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.measure_priming([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.measure_priming([('a', 'b', 1)] * 60)['total'] == 60
    assert m.measure_priming([('a', 'b', 9)])['peak'] == {'a': 9}
    # pre-seed pin: fresh accumulators only
    assert m.measure_priming([('p', 'a', 8), ('q', 'b', 1), ('p', 'b', 9)]) == {
        'total': 3, 'peak': {'p': 9, 'q': 1},
        'primed': {'p': ['a', 'b']}, 'numb': ['q'], 'sensitive': 'p'}
    return True


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def _sym(m):
    P = 'rows must be a list or tuple'
    for K in (L, T):
        _raises(TypeError, P, m.measure_priming, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (subject, stimulus, reaction) triple',
                m.measure_priming, [K(('a', 'b', 1))])
    _raises(ValueError, SM, m.measure_priming, [(S('a'), 'b', 1)])
    _raises(ValueError, TM, m.measure_priming, [('a', S('b'), 1)])
    _raises(ValueError, RM, m.measure_priming, [('a', 'b', I(1))])
    return True


def battery(m):
    _core(m)
    _late(m)
    _sym(m)
    return True


MUTANTS = [
    ('type(rows) not in (list, tuple)', 'not isinstance(rows, (list, tuple))'),
    ('not 1 <= len(rows) <= 60', 'not 1 <= len(rows) <= 61'),
    ('not 1 <= len(rows) <= 60', 'not 0 <= len(rows) <= 60'),
    ('type(row) not in (list, tuple)', 'not isinstance(row, (list, tuple))'),
    ('len(row) != 3', 'len(row) != 2'),
    ('type(subject) is not str', 'not isinstance(subject, str)'),
    ('type(stimulus) is not str', 'not isinstance(stimulus, str)'),
    ('type(reaction) is not int', 'not isinstance(reaction, int)'),
    ('not 1 <= len(subject) <= 16', 'not 1 <= len(subject) <= 17'),
    ('not 1 <= len(stimulus) <= 16', 'not 1 <= len(stimulus) <= 17'),
    ('not 1 <= reaction <= 9', 'not 1 <= reaction <= 10'),
    ('            per_pair[subject][stimulus] = reaction',
     '            per_pair[subject][stimulus] = 1'),
    ('elif reaction > per_pair[subject][stimulus]:',
     'elif reaction < per_pair[subject][stimulus]:'),
    ('            if per_pair[subject][stimulus] >= 8:',
     '            if per_pair[subject][stimulus] >= 9:'),
    ('if sensitive is None or len(primed[subject]) > len(primed[sensitive]):',
     'if sensitive is None or len(primed[subject]) < len(primed[sensitive]):'),
    ("'primed': primed", "'primed': peak"),
    ("'numb': sorted(numb)", "'numb': sorted(primed)"),
    ("'peak': peak", "'peak': primed"),
    ("'total': len(rows)", "'total': len(peak)"),
    ('        subject, stimulus, reaction = row',
     '        stimulus, subject, reaction = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True


def test_gap_pin_exact_cap_acceptance():
    # gap sweep: exact-cap 16-char labels accepted in each label
    # position, and on a late row
    assert mod.measure_priming([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.measure_priming([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.measure_priming([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2


def test_repair_pin_sensitive_none_documented():
    # 1889 repair: docstring documents the None case; behavior pinned
    doc = ' '.join(mod.__doc__.split())
    assert 'or None when no subject is primed' in doc
    assert mod.measure_priming([('s', 't', 1)]) == {
        'total': 1,
        'peak': {'s': 1},
        'primed': {},
        'numb': ['s'],
        'sensitive': None}
    assert mod.measure_priming([('a', 'x', 3), ('b', 'y', 7)]) == {
        'total': 2,
        'peak': {'a': 3, 'b': 7},
        'primed': {},
        'numb': ['a', 'b'],
        'sensitive': None}

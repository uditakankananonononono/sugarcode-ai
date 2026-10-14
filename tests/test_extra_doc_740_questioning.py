import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import questioning as mod

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
    assert mod.SCOPE == 'PARTIAL: first-word question classification over supplied strings, no real language parsing'
    assert len(mod.NOT_CLAIMED) >= 4 and 'pedagogy' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_QUESTIONS, mod.MAX_QUESTION) == (100, 80)
    assert 'what' in mod.OPENERS and 'is' in mod.CLOSERS


def _oracle(questions):
    """Independent: tokenize by splitting on the first space, word lists as sets."""
    openers = {'what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose'}
    closers = {'is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'will',
               'would', 'shall', 'should', 'have', 'has', 'may', 'might', 'must'}
    results = []
    for question in questions:
        words = question.split()
        first = words[0].lower() if words else ''
        if first in openers:
            results.append('open')
        elif first in closers:
            results.append('closed')
        else:
            results.append('other')
    counts = {'open': 0, 'closed': 0, 'other': 0}
    for label in results:
        counts[label] += 1
    return {'results': results, 'open': counts['open'], 'closed': counts['closed'],
            'other': counts['other']}


def _core(m):
    assert m.classify(['What is this?', 'Is it ready?', 'Indeed?']) == {
        'results': ['open', 'closed', 'other'], 'open': 1, 'closed': 1, 'other': 1}
    assert m.classify([]) == {'results': [], 'open': 0, 'closed': 0, 'other': 0}
    # the first word is lowercased before matching
    assert m.classify(['WHAT happened?', 'DOES it work?'])['results'] == ['open', 'closed']
    # leading whitespace does not hide the first word
    assert m.classify(['  How so?'])['results'] == ['open']
    # a single-character question is accepted and is other
    assert m.classify(['x'])['results'] == ['other']
    # whitespace-only questions have no first word and are other
    assert m.classify([' '])['results'] == ['other']
    assert m.classify(['\t', '\n', '  \t '])['other'] == 3
    assert m.classify(['\t \n '])['results'] == ['other']
    # only the first word decides
    assert m.classify(['Really what happened?'])['results'] == ['other']
    # every opener and a sample of closers classify
    for word in ('what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose'):
        assert m.classify(['%s is it?' % word])['results'] == ['open']
    for word in ('is', 'are', 'was', 'do', 'can', 'will', 'should', 'must'):
        assert m.classify(['%s it so?' % word])['results'] == ['closed']
    # a question mark is not required
    assert m.classify(['what now'])['results'] == ['open']
    # whom is not on the opener list
    assert m.classify(['whom did you see?'])['results'] == ['other']
    # tuples accepted
    assert m.classify(('why so?',))['open'] == 1
    rng = random.Random(740)
    words = ['what', 'Why', 'how', 'is', 'ARE', 'did', 'could', 'really', 'hmm', 'whence']
    for _ in range(400):
        questions = []
        for _ in range(rng.randint(0, 10)):
            first = rng.choice(words)
            pad = ' ' * rng.randint(0, 2)
            if rng.random() < 0.08:
                questions.append(rng.choice([' ', '\t', '\n', '  \t ']))
            else:
                questions.append(pad + first + ' rest of it?')
        assert m.classify(questions) == _oracle(questions)


def _late(m):
    QNS = 'questions must be a list or tuple'
    CAP = 'questions must contain at most 100 rows'
    STR = 'questions must be strings of 1 to 80 characters'
    good = ['what now?']
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, QNS, m.classify, bad)
    _raises(TypeError, QNS, m.classify, L(good * 101))          # subclass refused before the cap
    _raises(ValueError, CAP, m.classify, good * 101)
    assert m.classify(good * 100)['open'] == 100
    for bad in ('', 'x' * 81, None, 5, b'x', S('x'), LyingS('x'), I(1), ('x',)):
        _raises(ValueError, STR, m.classify, [bad])
        _raises(ValueError, STR, m.classify, ['what now?', bad])
    assert m.classify(['x' * 80])['other'] == 1
    _raises(ValueError, STR, m.classify, ['what now?'] * 6 + [5])
    # order: container, cap, strings
    _raises(TypeError, QNS, m.classify, L(good))
    _raises(ValueError, CAP, m.classify, [5] * 101)
    _raises(ValueError, STR, m.classify, [S('what now?')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    questions = ['what now?', 'is it?']
    r = mod.classify(questions)
    r['results'].append('bogus')
    assert questions == ['what now?', 'is it?']
    assert mod.classify(questions)['results'] == ['open', 'closed']


MUTANTS = [
    ("    if type(questions) not in (list, tuple):", "    if not isinstance(questions, (list, tuple)):"),
    ("    if len(questions) > MAX_QUESTIONS:", "    if len(questions) >= MAX_QUESTIONS:"),
    ("MAX_QUESTIONS = 100", "MAX_QUESTIONS = 101"),
    ("        if type(question) is not str or not 1 <= len(question) <= MAX_QUESTION:",
     "        if not isinstance(question, str) or not 1 <= len(question) <= MAX_QUESTION:"),
    ("not 1 <= len(question) <= MAX_QUESTION", "not 1 <= len(question) < MAX_QUESTION"),
    ("not 1 <= len(question) <= MAX_QUESTION", "not 0 <= len(question) <= MAX_QUESTION"),
    ("MAX_QUESTION = 80", "MAX_QUESTION = 81"),
    ("        first = tokens[0].lower() if tokens else ''", "        first = tokens[0].lower()"),
    ("        first = tokens[0].lower() if tokens else ''",
     "        first = tokens[-1].lower() if tokens else ''"),
    ("        first = tokens[0].lower() if tokens else ''", "        first = question.lower()"),
    ("        if first in OPENERS:", "        if first in CLOSERS:"),
    ("        elif first in CLOSERS:", "        elif first in OPENERS:"),
    ("OPENERS = ('what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose')",
     "OPENERS = ('what', 'why', 'how', 'when', 'where', 'who', 'which')"),
    ("OPENERS = ('what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose')",
     "OPENERS = ('what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose', 'whom')"),
    ("CLOSERS = ('is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'will',",
     "CLOSERS = ('is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'shall',"),
    ("            results.append('open')", "            results.append('closed')"),
    ("            results.append('closed')", "            results.append('open')"),
    ("            results.append('other')", "            results.append('open')"),
    ("            'open': sum(1 for r in results if r == 'open'),",
     "            'open': sum(1 for r in results if r != 'open'),"),
    ("            'closed': sum(1 for r in results if r == 'closed'),",
     "            'closed': sum(1 for r in results if r == 'open'),"),
    ("            'other': sum(1 for r in results if r == 'other')}",
     "            'other': sum(1 for r in results if r == 'other') + 1}"),
    ("    results = []", "    results = {}"),
    ("    for question in questions:\n        tokens = question.split()",
     "    for question in questions[:5]:\n        tokens = question.split()"),
    ("        first = tokens[0].lower() if tokens else ''", "        first = tokens[0].lower() if tokens else 'what'"),
    ("'questions must be a list or tuple'", "'questions must be a sequence'"),
    ("'questions must contain at most 100 rows'", "'questions must contain at most 99 rows'"),
    ("'questions must be strings of 1 to 80 characters'",
     "'questions must be strings of 1 to 79 characters'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

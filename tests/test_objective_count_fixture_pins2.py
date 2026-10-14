import pytest
from sugarcode.extra_doc import objective_count_fixture as mod


class L(list): pass
class T(tuple): pass
class D(dict): pass
class S(str): pass
class I(int): pass
class LyingS(str):
    def __eq__(self, other): return True
    def __ne__(self, other): return False
    def __hash__(self): return 0
class LyingI(int):
    def __lt__(self, other): return False
    def __le__(self, other): return True
    def __ge__(self, other): return True
    def __gt__(self, other): return True
    def __eq__(self, other): return True
    def __ne__(self, other): return False
    __hash__ = int.__hash__


def reject(exc, message, *args):
    with pytest.raises(exc) as e:
        mod.objective_count_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: formats supplied objective attempt/success count targets, no pedagogical objective writing'
    assert mod.NOT_CLAIMED == ('pedagogical objective writing', 'Bloom taxonomy validation', 'learning measurement', 'production readiness')
    assert mod.__doc__ == 'Row 1420, Learning Objective Writing.\n\nobjective_count_fixture formats supplied label and abstract attempt count\nx into a fixed objective string, requiring the ceiling of percent times x\nin hundredths successes. Supplied success count y meets inclusive target.\nReturns sorted objectives (label,text), met labels and percent. Zero attempts\nrequires zero successes. No pedagogical objective writing, Bloom taxonomy\nvalidation, learning measurement or educational recommendation is supplied.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 10; bool and all subclasses are refused.\npercent defaults to 80, an exact int from 0 to 100.\nValidation order: rows type, rows size, percent, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: pedagogical objective writing, Bloom taxonomy validation, learning measurement, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,10))
            for outer in (list,tuple):
                mod.objective_count_fixture(outer([row]))
                mod.objective_count_fixture(outer([('base',0,10),row]))
    for name in [chr(c) for c in range(0x80,0x100)] + ['中','١']:
        for rows in ([(name,0,10)],[('base',0,10),(name,0,10)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',rows)


def test_subclasses_at_every_input_level():
    good = ('a',0,10)
    for bad in (L([good]),T([good]),D(a=1)):
        reject(TypeError,'rows must be a list or tuple',bad)
    for bad in (L(good),T(good),D(a=1)):
        for prefix in ([],[('base',0,10)]):
            reject(ValueError,'each row must be a (label, x, y) triple',prefix+[bad])
    for bad in (S('a'),LyingS('a')):
        for prefix in ([],[('base',0,10)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',prefix+[(bad,0,10)])
    for bad in (I(0),LyingI(0),I(10**30),LyingI(10**30),True,False):
        for prefix in ([],[('base',0,10)]):
            reject(ValueError,'x must be a nonbool integer between 0 and 10',prefix+[('a',bad,10)])
            reject(ValueError,'y must be a nonbool integer between 0 and 10',prefix+[('a',0,bad)])
    for bad in (I(80),LyingI(80),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'percent must be a nonbool integer between 0 and 100',[good],bad)


def test_exact_output_types_and_key_order():
    expected = {'objectives': [('a', 'a: demonstrate 0 attempts with at least 0 successes'), ('z', 'z: demonstrate 2 attempts with at least 2 successes')], 'met': ['a', 'z'], 'percent': 80}
    actual = mod.objective_count_fixture([('z',2,3),('a',0,1)])
    def check(a,b):
        assert type(a) is type(b)
        if type(b) is dict:
            assert list(a) == list(b)
            for k in b: check(a[k],b[k])
        elif type(b) in (list,tuple):
            assert len(a) == len(b)
            for x,y in zip(a,b): check(x,y)
        else: assert a == b
    check(actual,expected)

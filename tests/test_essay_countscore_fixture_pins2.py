import pytest
from sugarcode.extra_doc import essay_countscore_fixture as mod


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
        mod.essay_countscore_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: supplied claim/evidence count bounded score, no essay scoring'
    assert mod.NOT_CLAIMED == ('essay scoring', 'text analysis', 'grading validity', 'production readiness')
    assert mod.__doc__ == 'Row 1476, Automated Essay Scoring.\n\nessay_countscore_fixture combines supplied claim count x twice and\nevidence count y three times, caps at cap. Returns sorted scores, capped\nstrictly beyond cap before limiting, total and cap. No essays are read;\ncounts are unverified. No actual essay scoring, text analysis, grading\nvalidity, semantic evidence quality or student judgment is supplied.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 10; bool and all subclasses are refused.\ncap defaults to 10, an exact int from 0 to 20.\nValidation order: rows type, rows size, cap, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: essay scoring, text analysis, grading validity, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,10))
            for outer in (list,tuple):
                mod.essay_countscore_fixture(outer([row]))
                mod.essay_countscore_fixture(outer([('base',0,10),row]))
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
    for bad in (I(10),LyingI(10),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'cap must be a nonbool integer between 0 and 20',[good],bad)


def test_exact_output_types_and_key_order():
    expected = {'scores': [('a', 3), ('z', 10)], 'capped': ['z'], 'total': 13, 'cap': 10}
    actual = mod.essay_countscore_fixture([('z',2,3),('a',0,1)])
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

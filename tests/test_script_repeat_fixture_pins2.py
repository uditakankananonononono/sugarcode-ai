import pytest
from sugarcode.extra_doc import script_repeat_fixture as mod


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
        mod.script_repeat_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: formats supplied cue/response repetition counts, no scripted teaching'
    assert mod.NOT_CLAIMED == ('scripted teaching', 'content validation', 'learning effectiveness', 'production readiness')
    assert mod.__doc__ == 'Row 1496, Scripted Instruction.\n\nscript_repeat_fixture formats supplied cue x and response y counts into\nfixed text for repeats iterations per label, in label then iteration order.\nReturns lines (label,one-based_iteration,text), cue_total and response_total.\nNo actual scripted teaching, lesson content, content validation, learner\nassessment, learning effectiveness or educational recommendation is supplied.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 10; bool and all subclasses are refused.\nrepeats defaults to 2, an exact int from 1 to 5.\nValidation order: rows type, rows size, repeats, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: scripted teaching, content validation, learning effectiveness, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,10))
            for outer in (list,tuple):
                mod.script_repeat_fixture(outer([row]))
                mod.script_repeat_fixture(outer([('base',0,10),row]))
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
    for bad in (I(2),LyingI(2),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'repeats must be a nonbool integer between 1 and 5',[good],bad)


def test_exact_output_types_and_key_order():
    expected = {'lines': [('a', 1, 'a: 0 cues; 1 responses'), ('a', 2, 'a: 0 cues; 1 responses'), ('z', 1, 'z: 2 cues; 3 responses'), ('z', 2, 'z: 2 cues; 3 responses')], 'cue_total': 4, 'response_total': 8}
    actual = mod.script_repeat_fixture([('z',2,3),('a',0,1)])
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

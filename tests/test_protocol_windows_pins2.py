import pytest
from sugarcode.extra_doc import protocol_windows as mod


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
        mod.protocol_windows(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: filters caller-supplied applicability windows for one integer marker, no treatment is selected'
    assert mod.NOT_CLAIMED == ('treatment selection', 'clinical safety', 'guideline validity', 'patient applicability', 'production readiness')
    assert mod.__doc__ == 'Row 1118, Treatment Protocol Selection.\n\nprotocol_windows treats x,y as caller-written inclusive applicability\nendpoints in either order. Return matches as (label,width) for windows\ncontaining marker, narrowest first then label; excluded as sorted labels\noutside marker; ambiguous as whether more than one window matches. It does\nnot pick a protocol, assign clinical meaning or advise treatment.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 100; bool and all subclasses are refused.\nmarker defaults to 50, an exact int from 0 to 100.\nValidation order: rows type, rows size, marker, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: treatment selection, clinical safety, guideline validity, patient applicability, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,100))
            for outer in (list,tuple):
                mod.protocol_windows(outer([row]))
                mod.protocol_windows(outer([('base',0,100),row]))
    for name in [chr(c) for c in range(0x80,0x100)] + ['中','١']:
        for rows in ([(name,0,100)],[('base',0,100),(name,0,100)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',rows)


def test_subclasses_at_every_input_level():
    good = ('a',0,100)
    for bad in (L([good]),T([good]),D(a=1)):
        reject(TypeError,'rows must be a list or tuple',bad)
    for bad in (L(good),T(good),D(a=1)):
        for prefix in ([],[('base',0,100)]):
            reject(ValueError,'each row must be a (label, x, y) triple',prefix+[bad])
    for bad in (S('a'),LyingS('a')):
        for prefix in ([],[('base',0,100)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',prefix+[(bad,0,100)])
    for bad in (I(0),LyingI(0),I(10**30),LyingI(10**30),True,False):
        for prefix in ([],[('base',0,100)]):
            reject(ValueError,'x must be a nonbool integer between 0 and 100',prefix+[('a',bad,100)])
            reject(ValueError,'y must be a nonbool integer between 0 and 100',prefix+[('a',0,bad)])
    for bad in (I(50),LyingI(50),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'marker must be a nonbool integer between 0 and 100',[good],bad)

import pytest
from sugarcode.extra_doc import assessment_pair_flags as mod


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
        mod.assessment_pair_flags(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: reports supplied self-rating disagreement beyond a fixed tolerance, no mental health is assessed'
    assert mod.NOT_CLAIMED == ('mental health assessment', 'diagnosis', 'clinical instrument validity', 'rating provenance', 'production readiness')
    assert mod.__doc__ == 'Row 1144, Mental Health Assessment.\n\nassessment_pair_flags takes two supplied integer ratings per caller label.\nReturns ranges as sorted (label,low,high), discrepant as sorted labels whose\nrating distance strictly exceeds tolerance, spread as largest distance.\nNo mental health instrument or diagnosis is interpreted. Ratings are supplied\nfixtures and no clinical meaning is assigned to their magnitude.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 10; bool and all subclasses are refused.\ntolerance defaults to 2, an exact int from 0 to 5.\nValidation order: rows type, rows size, tolerance, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: mental health assessment, diagnosis, clinical instrument validity, rating provenance, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,10))
            for outer in (list,tuple):
                mod.assessment_pair_flags(outer([row]))
                mod.assessment_pair_flags(outer([('base',0,10),row]))
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
        reject(ValueError,'tolerance must be a nonbool integer between 0 and 5',[good],bad)

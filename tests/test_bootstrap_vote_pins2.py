import pytest
from sugarcode.extra_doc import bootstrap_vote as mod


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
        mod.bootstrap_vote(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: enumerates majority outcomes of bootstrap-resampled supplied binary predictions'
    assert mod.NOT_CLAIMED == ('trained bootstrap models', 'generalization', 'independent voters', 'real stability', 'production readiness')
    assert mod.__doc__ == "Row 1095, Bootstrap Aggregation - Ensemble for stability.\n\nbootstrap_vote treats each row as a model's supplied binary predictions x,y\nfor two cases. Bootstrap draws model indices independently with replacement.\nFor each case return the exact probability of a strictly positive majority;\neven-draw ties count as zero. Returns majority_probability as two Fraction\nstrings in case order, changed as whether probabilities differ, draws as the\nnumber of model draws. No model is trained and no random draws are generated.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 1; bool and all subclasses are refused.\ndraws defaults to 3, an exact int from 1 to 5.\nValidation order: rows type, rows size, draws, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: trained bootstrap models, generalization, independent voters, real stability, production readiness.\n"


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,1))
            for outer in (list,tuple):
                mod.bootstrap_vote(outer([row]))
                mod.bootstrap_vote(outer([('base',0,1),row]))
    for name in [chr(c) for c in range(0x80,0x100)] + ['中','١']:
        for rows in ([(name,0,1)],[('base',0,1),(name,0,1)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',rows)


def test_subclasses_at_every_input_level():
    good = ('a',0,1)
    for bad in (L([good]),T([good]),D(a=1)):
        reject(TypeError,'rows must be a list or tuple',bad)
    for bad in (L(good),T(good),D(a=1)):
        for prefix in ([],[('base',0,1)]):
            reject(ValueError,'each row must be a (label, x, y) triple',prefix+[bad])
    for bad in (S('a'),LyingS('a')):
        for prefix in ([],[('base',0,1)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',prefix+[(bad,0,1)])
    for bad in (I(0),LyingI(0),I(10**30),LyingI(10**30),True,False):
        for prefix in ([],[('base',0,1)]):
            reject(ValueError,'x must be a nonbool integer between 0 and 1',prefix+[('a',bad,1)])
            reject(ValueError,'y must be a nonbool integer between 0 and 1',prefix+[('a',0,bad)])
    for bad in (I(3),LyingI(3),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'draws must be a nonbool integer between 1 and 5',[good],bad)

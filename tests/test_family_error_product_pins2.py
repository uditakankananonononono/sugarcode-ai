import pytest
from sugarcode.extra_doc import family_error_product as mod


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
        mod.family_error_product(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: computes independent-family any-error probabilities from supplied marginal risks'
    assert mod.NOT_CLAIMED == ('risk calibration', 'independence validity', 'actual false positives', 'statistical guarantee', 'production readiness')
    assert mod.__doc__ == 'Row 1086, Family-Wise Error Rate - Control any false positive.\n\nfamily_error_product treats x and y as marginal error percentages before\nand after a supplied adjustment, assumes independent family members. Any-error\nrisk is one minus the product of non-error probabilities. Returns old_risk\nand new_risk Fraction strings, within_limit as new risk at most limit percent,\nreduction as old minus new risk Fraction string. Inputs are supplied risks,\nnot p-values; the independence assumption and risk accuracy are not checked.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 100; bool and all subclasses are refused.\nlimit defaults to 10, an exact int from 0 to 100.\nValidation order: rows type, rows size, limit, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: risk calibration, independence validity, actual false positives, statistical guarantee, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,100))
            for outer in (list,tuple):
                mod.family_error_product(outer([row]))
                mod.family_error_product(outer([('base',0,100),row]))
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
    for bad in (I(10),LyingI(10),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'limit must be a nonbool integer between 0 and 100',[good],bad)

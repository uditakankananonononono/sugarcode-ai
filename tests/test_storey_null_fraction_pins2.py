import pytest
from sugarcode.extra_doc import storey_null_fraction as mod


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
        mod.storey_null_fraction(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: estimates Storey pi0 from supplied rational p-values and a fixed lambda grid'
    assert mod.NOT_CLAIMED == ('p-value validity', 'consistent pi0', 'adaptive FDR guarantee', 'data provenance', 'production readiness')
    assert mod.__doc__ == "Row 1090, Storey's Method - Adaptive FDR.\n\nstorey_null_fraction encodes supplied p-values x/(100+y) and lambda as\nlambda_tenths/10. Estimate raw_pi0=count(p>lambda)/(m*(1-lambda)), cap at\none for pi0. Returns above as sorted labels strictly above lambda, raw_pi0\nand pi0 as exact Fraction strings. Equality does not count. This estimates\na null fraction only; it does not run an adaptive rejection procedure or\nverify the estimator's statistical assumptions.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 100; bool and all subclasses are refused.\nlambda_tenths defaults to 5, an exact int from 1 to 9.\nValidation order: rows type, rows size, lambda_tenths, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: p-value validity, consistent pi0, adaptive FDR guarantee, data provenance, production readiness.\n"


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,100))
            for outer in (list,tuple):
                mod.storey_null_fraction(outer([row]))
                mod.storey_null_fraction(outer([('base',0,100),row]))
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
    for bad in (I(5),LyingI(5),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'lambda_tenths must be a nonbool integer between 1 and 9',[good],bad)

import pytest
from sugarcode.extra_doc import irr_grid_fixture as mod


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
        mod.irr_grid_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: finds exact roots on a finite integer-percent grid, no general IRR solver'
    assert mod.NOT_CLAIMED == ('general IRR solving', 'off-grid or multiple-root completeness', 'real valuation', 'financial advice', 'production readiness')
    assert mod.__doc__ == 'Row 1324, IRR Analysis.\n\nirr_grid_fixture treats each nonnegative x as a return count at period y\nand subtracts supplied outlay from its discounted sum. Checks every integer\npercent rate from 0 through 100 exactly. Returns roots as those integer\nrates with zero sum, unique if exactly one and outlay unchanged. This is\nfinite-grid equality testing, not general IRR: off-grid/negative rates and\nsigned cashflow multiple-root analysis are not solved. No valuation/advice.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 10; bool and all subclasses are refused.\noutlay defaults to 5, an exact int from 0 to 80.\nValidation order: rows type, rows size, outlay, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: general IRR solving, off-grid or multiple-root completeness, real valuation, financial advice, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,10))
            for outer in (list,tuple):
                mod.irr_grid_fixture(outer([row]))
                mod.irr_grid_fixture(outer([('base',0,10),row]))
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
    for bad in (I(5),LyingI(5),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'outlay must be a nonbool integer between 0 and 80',[good],bad)

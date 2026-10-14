import pytest
from sugarcode.extra_doc import wacc_weight_fixture as mod


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
        mod.wacc_weight_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: computes supplied positive weighted rate-count average, no real WACC estimate'
    assert mod.NOT_CLAIMED == ('real WACC estimate', 'debt or equity sourcing', 'tax shield inference', 'financial advice', 'production readiness')
    assert mod.__doc__ == 'Row 1328, WACC Calculation.\n\nwacc_weight_fixture weights supplied positive abstract rate x by positive\ny and reduces every rate uniformly by discount percent. Returns sorted\nweighted contributions as Fraction strings, mean sum and total weight.\nUniform discount is a fixture convention, not a debt-only tax shield. No debt,\nequity, tax, actual financing cost, market data or financial advice is inferred.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n1 to 10; bool and all subclasses are refused.\ndiscount defaults to 20, an exact int from 0 to 100.\nValidation order: rows type, rows size, discount, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: real WACC estimate, debt or equity sourcing, tax shield inference, financial advice, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,1,10))
            for outer in (list,tuple):
                mod.wacc_weight_fixture(outer([row]))
                mod.wacc_weight_fixture(outer([('base',1,10),row]))
    for name in [chr(c) for c in range(0x80,0x100)] + ['中','١']:
        for rows in ([(name,1,10)],[('base',1,10),(name,1,10)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',rows)


def test_subclasses_at_every_input_level():
    good = ('a',1,10)
    for bad in (L([good]),T([good]),D(a=1)):
        reject(TypeError,'rows must be a list or tuple',bad)
    for bad in (L(good),T(good),D(a=1)):
        for prefix in ([],[('base',1,10)]):
            reject(ValueError,'each row must be a (label, x, y) triple',prefix+[bad])
    for bad in (S('a'),LyingS('a')):
        for prefix in ([],[('base',1,10)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',prefix+[(bad,1,10)])
    for bad in (I(1),LyingI(1),I(10**30),LyingI(10**30),True,False):
        for prefix in ([],[('base',1,10)]):
            reject(ValueError,'x must be a nonbool integer between 1 and 10',prefix+[('a',bad,10)])
            reject(ValueError,'y must be a nonbool integer between 1 and 10',prefix+[('a',1,bad)])
    for bad in (I(20),LyingI(20),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'discount must be a nonbool integer between 0 and 100',[good],bad)

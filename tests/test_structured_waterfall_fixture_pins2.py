import pytest
from sugarcode.extra_doc import structured_waterfall_fixture as mod


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
        mod.structured_waterfall_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: allocates supplied payment counts down label-ordered caps, no structured-product valuation'
    assert mod.NOT_CLAIMED == ('structured product valuation', 'contract interpretation', 'market risk model', 'investment advice', 'production readiness')
    assert mod.__doc__ == 'Row 1368, Structured Products.\n\nstructured_waterfall_fixture pays supplied principal x plus coupon y\ncaps from funds in label order. Returns waterfall (label,paid,unpaid), left,\nfull labels with zero unpaid including zero cap, and total_paid. Labels are\nfixture priority, not contractual seniority. No real structured-product\nvaluation, contract interpretation, market risk model or advice is supplied.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 10; bool and all subclasses are refused.\nfunds defaults to 7, an exact int from 0 to 20.\nValidation order: rows type, rows size, funds, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: structured product valuation, contract interpretation, market risk model, investment advice, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,10))
            for outer in (list,tuple):
                mod.structured_waterfall_fixture(outer([row]))
                mod.structured_waterfall_fixture(outer([('base',0,10),row]))
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
    for bad in (I(7),LyingI(7),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'funds must be a nonbool integer between 0 and 20',[good],bad)


def test_exact_output_types_and_key_order():
    expected = {'waterfall': [('a', 1, 0), ('z', 5, 0)], 'left': 1, 'full': ['a', 'z'], 'total_paid': 6}
    actual = mod.structured_waterfall_fixture([('z',2,3),('a',0,1)])
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

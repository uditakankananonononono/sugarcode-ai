import pytest
from sugarcode.extra_doc import emh_sign_fixture as mod


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
        mod.emh_sign_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: counts supplied pairwise directional concordance, no EMH test'
    assert mod.NOT_CLAIMED == ('EMH test', 'statistical significance', 'market efficiency conclusion', 'financial advice', 'production readiness')
    assert mod.__doc__ == 'Row 1410, EMH Testing.\n\nemh_sign_fixture counts same-sign concordance for supplied signed count\npairs x and y, excluding either zero. Returns concordant, discordant and\nexcluded sorted labels, eligible count and meets for inclusive threshold\npercentage of concordant or None if no eligible pairs. No real EMH test,\nstatistical significance, efficiency conclusion or financial advice is given.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n-10 to 10; bool and all subclasses are refused.\nthreshold defaults to 60, an exact int from 0 to 100.\nValidation order: rows type, rows size, threshold, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: EMH test, statistical significance, market efficiency conclusion, financial advice, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,-10,10))
            for outer in (list,tuple):
                mod.emh_sign_fixture(outer([row]))
                mod.emh_sign_fixture(outer([('base',-10,10),row]))
    for name in [chr(c) for c in range(0x80,0x100)] + ['中','١']:
        for rows in ([(name,-10,10)],[('base',-10,10),(name,-10,10)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',rows)


def test_subclasses_at_every_input_level():
    good = ('a',-10,10)
    for bad in (L([good]),T([good]),D(a=1)):
        reject(TypeError,'rows must be a list or tuple',bad)
    for bad in (L(good),T(good),D(a=1)):
        for prefix in ([],[('base',-10,10)]):
            reject(ValueError,'each row must be a (label, x, y) triple',prefix+[bad])
    for bad in (S('a'),LyingS('a')):
        for prefix in ([],[('base',-10,10)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',prefix+[(bad,-10,10)])
    for bad in (I(-10),LyingI(-10),I(10**30),LyingI(10**30),True,False):
        for prefix in ([],[('base',-10,10)]):
            reject(ValueError,'x must be a nonbool integer between -10 and 10',prefix+[('a',bad,10)])
            reject(ValueError,'y must be a nonbool integer between -10 and 10',prefix+[('a',-10,bad)])
    for bad in (I(60),LyingI(60),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'threshold must be a nonbool integer between 0 and 100',[good],bad)


def test_exact_output_types_and_key_order():
    expected = {'concordant': ['z'], 'discordant': [], 'excluded': ['a'], 'meets': True, 'eligible': 1}
    actual = mod.emh_sign_fixture([('z',2,3),('a',0,1)])
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

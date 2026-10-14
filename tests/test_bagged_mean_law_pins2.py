import pytest
from sugarcode.extra_doc import bagged_mean_law as mod


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
        mod.bagged_mean_law(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: computes exact bootstrap mean expectation and variance from supplied paired readings'
    assert mod.NOT_CLAIMED == ('trained bagged models', 'generalization', 'independent data', 'bootstrap consistency', 'production readiness')
    assert mod.__doc__ == 'Row 1104, Bagging - Bootstrap aggregating.\n\nbagged_mean_law pools paired readings into an empirical population, draws\ndraws independent values with replacement and considers their mean. Returns\nexpected_mean as empirical mean Fraction string, mean_variance as empirical\npopulation variance divided by draws Fraction string, draws as supplied draw\ncount, population as pooled count. This gives exact bootstrap mean moments,\nnot trained model aggregation or a confidence interval.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n-10 to 10; bool and all subclasses are refused.\ndraws defaults to 3, an exact int from 1 to 5.\nValidation order: rows type, rows size, draws, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: trained bagged models, generalization, independent data, bootstrap consistency, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,-10,10))
            for outer in (list,tuple):
                mod.bagged_mean_law(outer([row]))
                mod.bagged_mean_law(outer([('base',-10,10),row]))
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
    for bad in (I(3),LyingI(3),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'draws must be a nonbool integer between 1 and 5',[good],bad)

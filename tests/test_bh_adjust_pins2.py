import pytest
from sugarcode.extra_doc import bh_adjust as mod


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
        mod.bh_adjust(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: computes exact BH step-up adjustments on supplied rational p-values'
    assert mod.NOT_CLAIMED == ('p-value validity', 'dependence assumptions', 'actual FDR guarantee', 'data provenance', 'production readiness')
    assert mod.__doc__ == 'Row 1089, Benjamini-Hochberg - FDR control.\n\nbh_adjust encodes supplied p-values x/(100+y), sorts ascending p then label,\nand reports BH adjusted p at rank i as min(1,min(m*p_j/(j+1) for j>=i)).\nReturns adjusted as (label,Fraction string) in p-rank order, rejected as\nlabels with adjusted p at most level percent in that order. It validates\nbounded numeric inputs, not p-value calibration or FDR dependence assumptions.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 100; bool and all subclasses are refused.\nlevel defaults to 5, an exact int from 1 to 100.\nValidation order: rows type, rows size, level, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: p-value validity, dependence assumptions, actual FDR guarantee, data provenance, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,100))
            for outer in (list,tuple):
                mod.bh_adjust(outer([row]))
                mod.bh_adjust(outer([('base',0,100),row]))
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
        reject(ValueError,'level must be a nonbool integer between 1 and 100',[good],bad)

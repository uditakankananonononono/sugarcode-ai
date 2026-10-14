import pytest
from sugarcode.extra_doc import local_null_odds as mod


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
        mod.local_null_odds(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: computes local null probability from supplied component masses and prior odds'
    assert mod.NOT_CLAIMED == ('density calibration', 'null truth', 'FDR guarantee', 'data provenance', 'production readiness')
    assert mod.__doc__ == 'Row 1091, Local FDR - Per-hypothesis FDR.\n\nlocal_null_odds treats x as positive supplied null density mass and y as\npositive supplied alternative mass at each observation. Prior null-to-alt\nodds is odds. Bayes local null probability is odds*x/(odds*x+y). Returns\nlocal_fdr as (label,Fraction string) sorted by label, alternative_favored as\nsorted labels with local null probability strictly below one half. No density\nis estimated and no empirical or frequentist FDR guarantee is made.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n1 to 100; bool and all subclasses are refused.\nodds defaults to 1, an exact int from 1 to 5.\nValidation order: rows type, rows size, odds, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: density calibration, null truth, FDR guarantee, data provenance, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,1,100))
            for outer in (list,tuple):
                mod.local_null_odds(outer([row]))
                mod.local_null_odds(outer([('base',1,100),row]))
    for name in [chr(c) for c in range(0x80,0x100)] + ['中','١']:
        for rows in ([(name,1,100)],[('base',1,100),(name,1,100)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',rows)


def test_subclasses_at_every_input_level():
    good = ('a',1,100)
    for bad in (L([good]),T([good]),D(a=1)):
        reject(TypeError,'rows must be a list or tuple',bad)
    for bad in (L(good),T(good),D(a=1)):
        for prefix in ([],[('base',1,100)]):
            reject(ValueError,'each row must be a (label, x, y) triple',prefix+[bad])
    for bad in (S('a'),LyingS('a')):
        for prefix in ([],[('base',1,100)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',prefix+[(bad,1,100)])
    for bad in (I(1),LyingI(1),I(10**30),LyingI(10**30),True,False):
        for prefix in ([],[('base',1,100)]):
            reject(ValueError,'x must be a nonbool integer between 1 and 100',prefix+[('a',bad,100)])
            reject(ValueError,'y must be a nonbool integer between 1 and 100',prefix+[('a',1,bad)])
    for bad in (I(1),LyingI(1),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'odds must be a nonbool integer between 1 and 5',[good],bad)

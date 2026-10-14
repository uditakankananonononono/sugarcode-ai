import pytest
from sugarcode.extra_doc import false_discovery_budget as mod


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
        mod.false_discovery_budget(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: selects a prefix under supplied posterior-null probability budget, no frequentist FDR is guaranteed'
    assert mod.NOT_CLAIMED == ('frequentist FDR guarantee', 'posterior calibration', 'null truth', 'data provenance', 'production readiness')
    assert mod.__doc__ == 'Row 1085, False Discovery Rate Control - Manage false positives.\n\nfalse_discovery_budget orders hypotheses by supplied ranking score x,\nascending with label ties. y is supplied posterior null probability percent.\nSelect the longest prefix whose average y is at most level; later prefixes\nmay become feasible after earlier ones fail. Returns selected in rank order,\nexpected_false as sum(y)/100 Fraction string, expected_fraction as average\ny/100 Fraction string, zero with no selections. This is posterior expected\nfalse-discovery budgeting, not a verified frequentist FDR controller.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 100; bool and all subclasses are refused.\nlevel defaults to 10, an exact int from 0 to 100.\nValidation order: rows type, rows size, level, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: frequentist FDR guarantee, posterior calibration, null truth, data provenance, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,100))
            for outer in (list,tuple):
                mod.false_discovery_budget(outer([row]))
                mod.false_discovery_budget(outer([('base',0,100),row]))
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
        reject(ValueError,'level must be a nonbool integer between 0 and 100',[good],bad)

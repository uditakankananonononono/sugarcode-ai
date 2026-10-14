import pytest
from sugarcode.extra_doc import pgx_rule_flags as mod


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
        mod.pgx_rule_flags(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: combines caller-supplied genotype and rule flag masks, no drug recommendation is made'
    assert mod.NOT_CLAIMED == ('drug recommendation', 'gene-drug validity', 'clinical safety', 'genotype interpretation', 'production readiness')
    assert mod.__doc__ == 'Row 1127, Pharmacogenomic Recommendations.\n\npgx_rule_flags treats x,y as caller-encoded four-bit genotype/rule flag\nmasks and reports (x&y)&mask. Returns flags as sorted (label,integer_mask),\nreview as sorted labels with any matched bit, bits as sorted (label,set_bit\nindices) with indices zero through three ascending. The flag meanings are\nnot interpreted; no gene-drug relation, medication or dose is recommended.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 15; bool and all subclasses are refused.\nmask defaults to 3, an exact int from 1 to 15.\nValidation order: rows type, rows size, mask, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: drug recommendation, gene-drug validity, clinical safety, genotype interpretation, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,15))
            for outer in (list,tuple):
                mod.pgx_rule_flags(outer([row]))
                mod.pgx_rule_flags(outer([('base',0,15),row]))
    for name in [chr(c) for c in range(0x80,0x100)] + ['中','١']:
        for rows in ([(name,0,15)],[('base',0,15),(name,0,15)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',rows)


def test_subclasses_at_every_input_level():
    good = ('a',0,15)
    for bad in (L([good]),T([good]),D(a=1)):
        reject(TypeError,'rows must be a list or tuple',bad)
    for bad in (L(good),T(good),D(a=1)):
        for prefix in ([],[('base',0,15)]):
            reject(ValueError,'each row must be a (label, x, y) triple',prefix+[bad])
    for bad in (S('a'),LyingS('a')):
        for prefix in ([],[('base',0,15)]):
            reject(ValueError,'label must be a printable ASCII string of 1 to 12 characters',prefix+[(bad,0,15)])
    for bad in (I(0),LyingI(0),I(10**30),LyingI(10**30),True,False):
        for prefix in ([],[('base',0,15)]):
            reject(ValueError,'x must be a nonbool integer between 0 and 15',prefix+[('a',bad,15)])
            reject(ValueError,'y must be a nonbool integer between 0 and 15',prefix+[('a',0,bad)])
    for bad in (I(3),LyingI(3),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'mask must be a nonbool integer between 1 and 15',[good],bad)

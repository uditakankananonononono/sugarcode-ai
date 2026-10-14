import pytest
from sugarcode.extra_doc import radiology_inventory as mod


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
        mod.radiology_inventory(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: renders an inventory of supplied integer observations and reference values, no radiology report is authored'
    assert mod.NOT_CLAIMED == ('radiology interpretation', 'medical report', 'diagnosis', 'measurement validity', 'production readiness')
    assert mod.__doc__ == 'Row 1122, Radiology Report Generation.\n\nradiology_inventory formats only caller-supplied integer observations x and\nreference y as exact values scaled by 10**precision. Returns inventory as\n(label,observed_Fraction_string,reference_Fraction_string) sorted by label,\nabove_reference as sorted labels with x>y, scale as 10**precision. This is\nan observation inventory, not a radiology report or interpretation; reference\nvalues have no inferred clinical meaning.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 100; bool and all subclasses are refused.\nprecision defaults to 1, an exact int from 0 to 5.\nValidation order: rows type, rows size, precision, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: radiology interpretation, medical report, diagnosis, measurement validity, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,100))
            for outer in (list,tuple):
                mod.radiology_inventory(outer([row]))
                mod.radiology_inventory(outer([('base',0,100),row]))
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
    for bad in (I(1),LyingI(1),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'precision must be a nonbool integer between 0 and 5',[good],bad)

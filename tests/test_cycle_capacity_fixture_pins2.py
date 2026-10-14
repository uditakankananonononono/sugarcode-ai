import pytest
from sugarcode.extra_doc import cycle_capacity_fixture as mod


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
        mod.cycle_capacity_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: calculates abstract capacity cycles, no asthma management'
    assert mod.NOT_CLAIMED == ('asthma management', 'inhaler regimen', 'clinical risk', 'treatment', 'production readiness')
    assert mod.__doc__ == 'Row 1159, Asthma Management.\n\ncycle_capacity_fixture computes ceil((x+reserve)/y) for supplied positive\nabstract load x and capacity y. Returns label-sorted cycles (label,count,\nspare_capacity_in_last_cycle), total_cycles and full labels with zero spare.\nNo inhaler use, lung function, safety or asthma care is interpreted.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n1 to 10; bool and all subclasses are refused.\nreserve defaults to 1, an exact int from 0 to 5.\nValidation order: rows type, rows size, reserve, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: asthma management, inhaler regimen, clinical risk, treatment, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,1,10))
            for outer in (list,tuple):
                mod.cycle_capacity_fixture(outer([row]))
                mod.cycle_capacity_fixture(outer([('base',1,10),row]))
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
    for bad in (I(1),LyingI(1),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'reserve must be a nonbool integer between 0 and 5',[good],bad)

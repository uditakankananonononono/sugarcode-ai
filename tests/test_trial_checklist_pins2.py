import pytest
from sugarcode.extra_doc import trial_checklist as mod


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
        mod.trial_checklist(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: compares supplied required and satisfied checklist masks, no clinical eligibility is determined'
    assert mod.NOT_CLAIMED == ('clinical eligibility', 'trial suitability', 'criterion validity', 'patient safety', 'production readiness')
    assert mod.__doc__ == 'Row 1128, Clinical Trial Matching.\n\ntrial_checklist treats x as four-bit required checklist mask and y as\nfour-bit satisfied mask. Missing bits are required and not satisfied.\nReturns missing as sorted (label,missing_mask), counts as sorted (label,\nmissing_bit_count), within_allowance as sorted labels with missing count at\nmost allowed_missing. Extra satisfied bits do not count against requirements.\nThis compares caller checklists only, not clinical eligibility or trial fit.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 15; bool and all subclasses are refused.\nallowed_missing defaults to 0, an exact int from 0 to 4.\nValidation order: rows type, rows size, allowed_missing, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: clinical eligibility, trial suitability, criterion validity, patient safety, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,15))
            for outer in (list,tuple):
                mod.trial_checklist(outer([row]))
                mod.trial_checklist(outer([('base',0,15),row]))
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
    for bad in (I(0),LyingI(0),I(10**30),LyingI(10**30),True,False):
        reject(ValueError,'allowed_missing must be a nonbool integer between 0 and 4',[good],bad)

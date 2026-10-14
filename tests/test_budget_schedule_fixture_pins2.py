import pytest
from sugarcode.extra_doc import budget_schedule_fixture as mod


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
        mod.budget_schedule_fixture(*args)
    assert str(e.value) == message


def test_exact_disclaimer():
    assert mod.SCOPE == 'PARTIAL: allocates abstract unit budgets to supplied tasks, no addiction treatment planning'
    assert mod.NOT_CLAIMED == ('addiction treatment', 'clinical prioritization', 'dose or care plan', 'safety', 'production readiness')
    assert mod.__doc__ == 'Row 1148, Addiction Treatment Planning.\n\nbudget_schedule_fixture allocates budget units in ascending label order.\nEach supplied task needs max(0,x-y), where x is requested units and y is\nalready reserved units. Returns allocations (label,given,missing), unused\nbudget and complete (every missing count zero). Units are abstract and this\ndoes not design, recommend or validate addiction treatment.\nInputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an\nexact list or tuple (label, x, y). label is an exact printable ASCII str\nof 1 to 12 characters, unique across rows. x and y are exact ints from\n0 to 10; bool and all subclasses are refused.\nbudget defaults to 7, an exact int from 0 to 80.\nValidation order: rows type, rows size, budget, then each row in input\norder (shape, label, x, y), then duplicate labels.\nNOT_CLAIMED: addiction treatment, clinical prioritization, dose or care plan, safety, production readiness.\n'


def test_every_printable_and_nonascii_text_slot():
    # One text slot per row, exercised first and later, in both row containers.
    for name in [' '] + [chr(c) for c in range(0x21,0x7f)] + ['A~ z']:
        for container in (list,tuple):
            row = container((name,0,10))
            for outer in (list,tuple):
                mod.budget_schedule_fixture(outer([row]))
                mod.budget_schedule_fixture(outer([('base',0,10),row]))
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
        reject(ValueError,'budget must be a nonbool integer between 0 and 80',[good],bad)

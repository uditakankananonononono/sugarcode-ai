import copy
import re
import pytest
from sugarcode.extra_doc.key_management import audit

class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
class LyingInt(int):
    def __gt__(self, other): return False
    def __add__(self, other): return 0

OK = [('a', 0, 5, False), ('b', 0, 5, False)]

def refused(keys, today, warn, message):
    with pytest.raises(ValueError, match='^' + re.escape(message) + '$'):
        audit(keys, today, warn)

@pytest.mark.parametrize('container', [L, T])
def test_container_subclasses(container):
    refused(container(OK), 10, 14, 'keys: list required')
    refused([OK[0], container(OK[1])], 10, 14,
            'keys[1]: (name, created_day, rotation_days, revoked) required')

@pytest.mark.parametrize('slot', [0, 1, 2, 3])
def test_slot_subclasses_nonfirst(slot):
    row = list(OK[1])
    row[slot] = S('b') if slot == 0 else I(row[slot])
    messages = ['keys[1] name: non-empty string up to 60 characters required',
                'keys[1] created_day: integer required',
                'keys[1] rotation_days: integer required', 'keys[1] revoked: bool required']
    refused([OK[0], tuple(row)], 10, 14, messages[slot])

@pytest.mark.parametrize('which', ['today', 'warn_days'])
def test_parameter_subclasses(which):
    refused(OK, I(10) if which == 'today' else 10,
            I(14) if which == 'warn_days' else 14, which + ': integer required')

def test_lying_date_subclass_refused():
    refused([OK[0], ('b', LyingInt(11), 5, False)], 10, 14,
            'keys[1] created_day: integer required')

@pytest.mark.parametrize('keys,today,warn,message', [
    (None,10,14,'keys: list required'), ([],10,14,'keys: 1 to 500 entries required'),
    ([None]*501,10,14,'keys: 1 to 500 entries required'),
    (OK,-1,14,'today: must be within 0 to 1000000'),
    (OK,1000001,14,'today: must be within 0 to 1000000'),
    (OK,10,-1,'warn_days: must be within 0 to 3650'),
    (OK,10,3651,'warn_days: must be within 0 to 3650'),
    ([OK[0],None],10,14,'keys[1]: (name, created_day, rotation_days, revoked) required'),
    ([OK[0],('b',0,5)],10,14,'keys[1]: 4 entries required'),
    ([OK[0],('b',0,5,False,1)],10,14,'keys[1]: 4 entries required'),
    ([OK[0],('',0,5,False)],10,14,'keys[1] name: non-empty string up to 60 characters required'),
    ([OK[0],('a',0,5,False)],10,14,'keys[1]: duplicate key a'),
    ([OK[0],('b',-1,5,False)],10,14,'keys[1] created_day: must be within 0 to 1000000'),
    ([OK[0],('b',1000001,5,False)],10,14,'keys[1] created_day: must be within 0 to 1000000'),
    ([OK[0],('b',11,5,False)],10,14,'keys[1] created_day: must not be after today'),
    ([OK[0],('b',0,0,False)],10,14,'keys[1] rotation_days: must be within 1 to 3650'),
    ([OK[0],('b',0,3651,False)],10,14,'keys[1] rotation_days: must be within 1 to 3650'),
    ([OK[0],('b',0,5,0)],10,14,'keys[1] revoked: bool required'),
])
def test_exact_errors(keys, today, warn, message):
    refused(keys, today, warn, message)

@pytest.mark.parametrize('outer', [list, tuple])
@pytest.mark.parametrize('row_type', [list, tuple])
def test_plain_containers_default_and_boundaries(outer, row_type):
    keys = outer([row_type(('a', 0, 14, False)), row_type(('b', 0, 15, False))])
    before = copy.deepcopy(keys)
    assert [r['status'] for r in audit(keys, 0)['keys']] == ['due_soon', 'ok']
    assert audit(keys, 0) == audit(keys, 0, 14)
    assert keys == before
    for created in (0, 1000000):
        for rotation in (1, 3650):
            for warn in (0, 3650):
                r = audit([('x'*60, created, rotation, False)], created, warn)['keys'][0]
                assert r['due_day'] == created + rotation and r['age_days'] == 0
                assert r['days_left'] == rotation

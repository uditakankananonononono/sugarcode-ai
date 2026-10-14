import copy
import re
from fractions import Fraction
import pytest
from sugarcode.extra_doc.privacy_by_design import audit, STATUS_NOTE
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
class LyingInt(int):
    def __gt__(self, other): return False
    def __rsub__(self, other): return 0

FIELDS = [('a',True,0,0,1), ('b',False,3,0,1)]

def refused(fields,today,message):
    with pytest.raises(ValueError,match='^'+re.escape(message)+'$'):
        audit(fields,today)

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses(container):
    refused(container(FIELDS),1,'fields: list required')
    refused([FIELDS[0],container(FIELDS[1])],1,
            'fields[1]: (name, needed, sensitivity, collected_day, retention_days) required')

@pytest.mark.parametrize('slot',range(5))
def test_slot_subclasses_nonfirst(slot):
    row=list(FIELDS[1]);row[slot]=S(row[slot]) if slot==0 else I(row[slot])
    messages=['name: non-empty string up to 60 characters required','needed: bool required',
              'sensitivity: integer required','collected_day: integer required','retention_days: integer required']
    refused([FIELDS[0],tuple(row)],1,'fields[1] '+messages[slot])

def test_today_and_lying_collected_subclass():
    refused(FIELDS,I(1),'today: integer required')
    refused([FIELDS[0],('b',False,0,LyingInt(2),1)],1,'fields[1] collected_day: integer required')

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_full_result_and_unchanged(outer,row):
    fields=outer(row(f) for f in FIELDS);before=copy.deepcopy(fields)
    result=audit(fields,1)
    assert result=={'fields':[{'name':'a','needed':True,'sensitivity':0,'age_days':1,'days_over':0,'retention':'due'},
                             {'name':'b','needed':False,'sensitivity':3,'age_days':1,'days_over':0,'retention':'due'}],
                    'unneeded':['b'],'overdue':[],'needed_share':Fraction(1,2),'unneeded_sensitivity':3,
                    'status_note':'PARTIAL: minimisation and retention arithmetic over supplied fields only; no judgment of lawfulness or of what should be collected'}
    assert result['status_note']==STATUS_NOTE
    assert fields==before

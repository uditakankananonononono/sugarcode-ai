import copy
import re
from fractions import Fraction
import pytest
from sugarcode.extra_doc.compliance_implementation import coverage, STATUS_NOTE

class L(list): pass
class T(tuple): pass
class S(str): pass

REQS = [('r0','a'), ('r1','b')]
CTLS = [('c0','a',['r0']), ('c1','b',['r0','r1'])]

def refused(reqs, ctls, message):
    with pytest.raises(ValueError, match='^'+re.escape(message)+'$'):
        coverage(reqs, ctls)

@pytest.mark.parametrize('container', [L,T])
@pytest.mark.parametrize('which', ['requirements','controls','refs'])
def test_container_subclasses(container, which):
    reqs, ctls = copy.deepcopy(REQS), copy.deepcopy(CTLS)
    if which == 'requirements':
        refused(container(reqs), ctls, 'requirements: list required')
        reqs[1] = container(reqs[1])
        refused(reqs, ctls, 'requirements[1]: (rid, title) required')
    elif which == 'controls':
        refused(reqs, container(ctls), 'controls: list required')
        ctls[1] = container(ctls[1])
        refused(reqs, ctls, 'controls[1]: (cid, title, rids) required')
    else:
        ctls[1] = ('c1','b',container(['r0','r1']))
        refused(reqs, ctls, 'controls[1] rids: list required')

@pytest.mark.parametrize('which', ['requirements','controls'])
@pytest.mark.parametrize('slot', [0,1])
def test_string_subclasses_nonfirst(which, slot):
    reqs, ctls = copy.deepcopy(REQS), copy.deepcopy(CTLS)
    rows = reqs if which == 'requirements' else ctls
    row = list(rows[1]); row[slot] = S(row[slot]); rows[1] = tuple(row)
    field, cap = ('id',20) if slot == 0 else ('title',80)
    refused(reqs,ctls,which+'[1] '+field+': non-empty string up to '+str(cap)+' characters required')

def test_ref_string_subclass_nonfirst():
    refused(REQS,[CTLS[0],('c1','b',['r0',S('r1')])],
            'controls[1] rids[1]: non-empty string up to 20 characters required')

@pytest.mark.parametrize('outer', [list,tuple])
@pytest.mark.parametrize('row', [list,tuple])
@pytest.mark.parametrize('refs', [list,tuple])
def test_full_result_keys_plain_containers_and_unchanged(outer,row,refs):
    reqs = outer(row(r) for r in REQS)
    ctls = outer(row((c,t,refs(rs))) for c,t,rs in CTLS)
    before = copy.deepcopy((reqs,ctls))
    assert coverage(reqs,ctls) == {
        'requirements':[{'rid':'r0','title':'a','controls':['c0','c1']},
                        {'rid':'r1','title':'b','controls':['c1']}],
        'uncovered':[], 'orphan_controls':[], 'covered_share':Fraction(1),
        'max_controls_per_requirement':2,
        'status_note':'PARTIAL: coverage bookkeeping over supplied ids only; no judgment of whether any control satisfies any requirement or regulation'}
    assert coverage(reqs,ctls)['status_note'] == STATUS_NOTE
    assert (reqs,ctls) == before

def test_empty_controls_full_result():
    result = coverage([('r','a')], [])
    assert result['requirements'] == [{'rid':'r','title':'a','controls':[]}]
    assert result['uncovered'] == ['r'] and result['orphan_controls'] == []
    assert result['covered_share'] == Fraction(0) and result['max_controls_per_requirement'] == 0

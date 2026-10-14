import pytest
from sugarcode.extra_doc.authorization_design526 import evaluate_role_policy as run

P=[('reader','doc','read','allow')]
R=[('amy','reader','doc','read')]


def test_deny_override_absence_and_each_key_slot():
    assert run(P,R)['decisions']==[('amy','reader','doc','read',True)]
    assert run(P+[('reader','doc','read','deny')],R)['decisions'][0][-1] is False
    assert run([('reader','doc','read','deny')],R)['decisions'][0][-1] is False
    for slot in range(1,4):
        row=list(R[0]);row[slot]='other'
        assert run(P,[tuple(row)])['decisions'][0][-1] is False
    assert run(P,[('bob',*R[0][1:])])['decisions'][0][-1] is True


@pytest.mark.parametrize('which',range(2))
@pytest.mark.parametrize('size',[0,33])
def test_outer_caps(which,size):
    args=[P,R];args[which]=[None]*size
    with pytest.raises(ValueError,match='^row count must be 1..32$'):run(*args)


@pytest.mark.parametrize('which',range(2))
@pytest.mark.parametrize('size',[0,3,5])
def test_arity_precedence(which,size):
    args=[P,R];args[which]=[(None,)*size]
    with pytest.raises(ValueError,match='^wrong row arity$'):run(*args)


@pytest.mark.parametrize('which,slot',[(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(1,3)])
@pytest.mark.parametrize('bad',[None,1,True,b'a',[]])
def test_each_identifier_slot_type(which,slot,bad):
    args=[P,R];row=list(args[which][0]);row[slot]=bad;args[which]=[tuple(row)]
    with pytest.raises(TypeError,match='^exact string label required$'):run(*args)


@pytest.mark.parametrize('bad',[None,1,True,b'allow',[]])
def test_effect_type(bad):
    with pytest.raises(TypeError,match='^exact string effect required$'):run([('r','doc','read',bad)],R)


@pytest.mark.parametrize('bad',['ALLOW','unknown','', 'allow '*100])
def test_effect_enum(bad):
    with pytest.raises(ValueError,match='^effect must be allow or deny$'):run([('r','doc','read',bad)],R)


def test_duplicate_exact_rules_requests_and_permutations():
    with pytest.raises(ValueError,match='^duplicate policy rule$'):run(P*2,R)
    with pytest.raises(ValueError,match='^duplicate policy request$'):run(P,R*2)
    policy=P+[('reader','doc','read','deny')];requests=R+[('bob','reader','doc','read')]
    assert run(policy,requests)==run(list(reversed(policy)),list(reversed(requests)))
    p=[('r_'+str(i),'doc','read','allow') for i in range(32)]
    q=[('s_'+str(i),'r_'+str(i),'doc','read') for i in range(32)]
    assert all(row[-1] for row in run(p,q)['decisions'])

import copy
import random
import string
import pytest
from sugarcode.extra_doc import adherence_records1193 as m

SCOPE = 'PARTIAL: supplied schedule/log IDs only; no medication-taking assessment'
NC = ['does not verify medication was taken',
      'does not validate prescriptions, doses or timing',
      'does not estimate adherence or health outcomes',
      'does not recommend medication changes']


def oracle(schedule, logs):
    schedule = [tuple(r) for r in schedule];logs = [tuple(r) for r in logs]
    persons = sorted({r[0] for r in schedule+logs})
    missing = sorted(r for r in schedule if r not in logs)
    unexpected = sorted({r for r in logs if r not in schedule})
    repeated = sorted({r for r in logs if logs.count(r) > 1})
    rows = []
    for p in persons:
        expected = [r for r in schedule if r[0] == p]
        absent = [r for r in missing if r[0] == p]
        rows.append((p,len(expected),len(expected)-len(absent),len(absent)))
    return dict(people=rows,missing=missing,unexpected=unexpected,repeated=repeated,scope=SCOPE,not_claimed=NC)


def test_hand_scope_freshness():
    s=[('a','d1'),['a','d2'],('b','d1')];l=[('a','d1'),['a','d1'],('z','d9')]
    before=copy.deepcopy((s,l));out=m.reconcile(s,l)
    assert out==dict(people=[('a',2,1,1),('b',1,0,1),('z',0,0,0)],missing=[('a','d2'),('b','d1')],unexpected=[('z','d9')],repeated=[('a','d1')],scope=SCOPE,not_claimed=NC)
    assert (s,l)==before
    out['not_claimed'][0]+='x';out['missing'].clear()
    assert m.reconcile(s,l)==oracle(s,l)
    assert m.reconcile([('a','d1')],[])==oracle([('a','d1')],[])
    assert m.reconcile([('a','d1')],[('a','d1')]*3)==oracle([('a','d1')],[('a','d1')]*3)
    assert m.NOT_CLAIMED==tuple(NC) and m.SCOPE==SCOPE
    assert m.__doc__.split('\n\n')[1]==('PARTIAL: supplied identifier reconciliation only. No verification that any\n'
        'medication was taken, prescribed correctly or safe. No medical advice.')


def test_random_oracle():
    rng=random.Random(1193);pool=[(p,e) for p in 'ab_0X' for e in ['d1','d2','A','_']]
    for _ in range(500):
        s=rng.sample(pool,rng.randrange(1,len(pool)+1));l=[rng.choice(pool) for _ in range(rng.randrange(129))]
        assert m.reconcile(tuple(s),[list(r) if i%2 else r for i,r in enumerate(l)])==oracle(s,l)


class L(list):pass
class T(tuple):pass
class S(str):pass


def bad(exc,msg,s,l):
    with pytest.raises(exc) as e:m.reconcile(s,l)
    assert str(e.value)==msg


def test_invalid_caps_precedence():
    base=[('p','e')]
    for name,which in [('schedule',0),('logs',1)]:
        for x in (None,{},'ab',L(base),T(base)):
            args=[base,[]];args[which]=x;bad(TypeError,name+' must be an exact list or tuple',*args)
        for x in (None,{},'ab',L(('p','e')),T(('p','e'))):
            args=[base,[]];args[which]=[x];bad(TypeError,name+' row must be an exact list or tuple',*args)
        for x in ([],['p'],['p','e','z']):
            args=[base,[]];args[which]=[x];bad(ValueError,name+' row must have two identifiers',*args)
    bad(ValueError,'schedule count outside declared range',[],None)
    bad(ValueError,'schedule count outside declared range',[None]*65,None)
    bad(ValueError,'logs count outside declared range',base,[None]*129)
    bad(ValueError,'scheduled pairs must be unique',base*2,None)
    bad(ValueError,'at most16 people allowed',[(str(i),'e') for i in range(17)],[])
    bad(ValueError,'at most16 people allowed',base,[(str(i),'e') for i in range(16)])
    schedule=[('p'+str(i%16),'e'+str(i)) for i in range(64)]
    assert m.reconcile(schedule,schedule*2)==oracle(schedule,schedule*2)
    bad(TypeError,'identifier must be an exact string',base,[(str(i),'e') for i in range(17)]+[(None,'e')])


def test_identifiers_all_positions():
    for which in range(2):
        for slot in range(2):
            for value in (None,1,True,b'a',S('a')):
                args=[[['p','e']],[['p','e']]];args[which][0][slot]=value
                bad(TypeError,'identifier must be an exact string',*args)
            for value in ('','a'*25,'é','Α','Ａ','🙂','a b','a\n'):
                args=[[['p','e']],[['p','e']]];args[which][0][slot]=value
                bad(ValueError,'identifier must be 1..24 ASCII word characters',*args)
    for c in string.printable+'éΑＡЖ🙂\u200b\x00':
        if c in string.ascii_letters+string.digits+'_':
            assert m.reconcile([(c,c)],[(c,c)])['people']==[(c,1,1,0)]
        else:bad(ValueError,'identifier must be 1..24 ASCII word characters',[(c,'e')],[])
    assert m.reconcile([('a'*24,'b'*24)],[])['missing']==[('a'*24,'b'*24)]

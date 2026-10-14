import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import value_ranking483_x3 as mod
from sugarcode.extra_doc.value_ranking483_x3 import analyze_value_ranking as run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 1), ('b', 2)]
INTS=[(1, 1, 32)]
B={sl:(lo,hi) for sl,lo,hi in INTS}
UNIQ1=[1]
UNIQC=[]
def oracle(rows):
    r=sorted(rows,key=lambda x:x[1])
    return {'order':[x[0] for x in r],'contiguous':[x[1] for x in r]==list(range(1,len(r)+1)),'values_adopted':False}

def gen(rng,count=None):
    count=count or rng.randint(1,32)
    for sl in UNIQ1:count=min(count,B[sl][1]-B[sl][0]+1)
    labels=['l%02d'%i for i in range(count)];rng.shuffle(labels)
    cols={}
    for slot,lo,hi in INTS:
        small=rng.random()<0.5
        top=min(hi,lo+3) if small else hi
        if slot in UNIQ1:
            width=top-lo+1
            if width<count:top=hi
            cols[slot]=rng.sample(range(lo,top+1),count)
        else:cols[slot]=[rng.randint(lo,top) for _ in range(count)]
    for slots in UNIQC:
        seen=set()
        for i in range(count):
            for _ in range(500):
                pair=tuple(rng.randint(B[sl][0],B[sl][1]) for sl in slots)
                if pair not in seen:break
            seen.add(pair)
            for sl,value in zip(slots,pair):cols[sl][i]=value
    rows=[]
    for i in range(count):
        row=[labels[i]]+[cols[sl][i] for sl,_,_ in INTS]
        rows.append(tuple(row) if rng.random()<0.5 else row)
    return rows
def test_hand_literals():
    assert run([('b',3),('a',1),('c',2)])=={'order':['a','c','b'],'contiguous':True,'values_adopted':False}
    assert run([('a',2)])['contiguous'] is False
    assert run([('a',1),('b',3)])['contiguous'] is False
def test_independent_oracle_random_and_input_unchanged():
    rng=random.Random(483)
    for _ in range(400):
        rows=gen(rng);before=copy.deepcopy(rows)
        assert run(rows)==oracle([tuple(r) for r in rows]) and rows==before
def test_not_claimed_scope_and_flag():
    assert 'NOT_CLAIMED: adopted values, principles being right or external effects' in mod.__doc__
    assert run(ROWS)['values_adopted'] is False
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^values: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^values: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad',[None,'ab',{},1,iter([])])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^values: exact list or tuple required$'):run(bad)
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),(None,TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('\u00e9',ValueError,'label must be 1..24 ASCII word characters'),('a-b',ValueError,'label must be 1..24 ASCII word characters'),('a.b',ValueError,'label must be 1..24 ASCII word characters'),('a b',ValueError,'label must be 1..24 ASCII word characters'),('a/b',ValueError,'label must be 1..24 ASCII word characters'),('a@b',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'values: row count outside declared range'),([None]*33,'values: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'values: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'value labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))
    r[0]='_';assert run([r])
@pytest.mark.parametrize('slot,lo,hi',INTS)
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(1.0,TypeError,'exact nonbool integer required'),(None,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
    for ok in (lo,hi):
        r=list(ROWS[1]);r[slot]=ok
        if not (slot in UNIQ1 and ok==ROWS[0][slot]) and not any(slot in u for u in UNIQC):run([ROWS[0],tuple(r)])
def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^value labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    if not UNIQ1 and not UNIQC:assert run([ROWS[0],tuple(second)])
def test_extra_unique_keys():
    for slot in UNIQ1:
        second=list(ROWS[1]);second[slot]=ROWS[0][slot];second[0]='other'
        with pytest.raises(ValueError,match='^'+[m for sl,m in [((1,), 'value ranks must be unique')] if sl==(slot,)][0]+'$'):run([ROWS[0],tuple(second)])
    for slots in UNIQC:
        msg=[m for sl,m in [((1,), 'value ranks must be unique')] if sl==slots][0]
        second=list(ROWS[1]);second[0]='other'
        for sl in slots:second[sl]=ROWS[0][sl]
        with pytest.raises(ValueError,match='^'+msg+'$'):run([ROWS[0],tuple(second)])
        for keep in slots:
            third=list(second)
            for sl in slots:
                if sl!=keep:third[sl]=ROWS[1][sl]
            assert run([ROWS[0],tuple(third)])
def test_exact_cap_32_rows_accepted():
    rows=gen(random.Random(483),32)
    assert len(rows)==32 and run(rows)==oracle([tuple(r) for r in rows])
    with pytest.raises(ValueError,match='^values: row count outside declared range$'):run(rows+[rows[0]])
def test_mixed_row_containers():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    rev=[tuple(ROWS[1]),list(ROWS[0])]
    assert run(rev)==run([tuple(r) for r in rev])
def test_validation_precedence_label_before_integer():
    row=list(ROWS[1]);row[0]='a-b';row[1]=True
    with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],row])
    row[0]=None;row[1]=1000000001
    with pytest.raises(TypeError,match='^exact string label required$'):run([ROWS[0],row])
def test_all_row_shapes_before_content():
    row=list(ROWS[0]);row[0]='a-b'
    with pytest.raises(ValueError,match='^values: wrong row arity$'):run([row,ROWS[1][:-1]])
    with pytest.raises(TypeError,match='^values: exact list or tuple row required$'):run([row,None])
def test_integer_field_order_with_multiple_bad_values():
    slots=[x[0] for x in INTS]
    for first,second in zip(slots,slots[1:]):
        row=list(ROWS[1]);row[first]=True;row[second]=1000000001
        with pytest.raises(TypeError,match='^exact nonbool integer required$'):run([ROWS[0],row])
        row=list(ROWS[1]);row[first]=1000000001;row[second]=True
        with pytest.raises(ValueError,match='^integer outside declared range$'):run([ROWS[0],row])
def test_label_sort_independent_of_columns():
    base=list(ROWS[0]);other=list(ROWS[0])
    rows=[tuple(['b']+base[1:]),tuple(['a']+other[1:])]
    for slot in UNIQ1:
        rows[1]=rows[1][:slot]+(ROWS[1][slot],)+rows[1][slot+1:]
    for slots in UNIQC:
        for sl in slots:rows[1]=rows[1][:sl]+(ROWS[1][sl],)+rows[1][sl+1:]
    assert run(rows)==oracle(rows)
    assert 483 in (466,467,468,469) or run(list(reversed(rows)))==oracle(rows)


def test_row_arity_both_directions_and_single_row_cap_edge():
    for bad in (ROWS[1][:-1],tuple(ROWS[1])+(0,),list(ROWS[1])+[0],()):
        with pytest.raises(ValueError,match='^values: wrong row arity$'):run([ROWS[0],bad])
    assert run([ROWS[0]])
    for count in (0,33):
        with pytest.raises(ValueError,match='^values: row count outside declared range$'):run([ROWS[0]]*count)
    with pytest.raises(TypeError,match='^values: exact list or tuple row required$'):run([ROWS[0],'ab'])
    with pytest.raises(TypeError,match='^values: exact list or tuple row required$'):run([ROWS[0],{}])

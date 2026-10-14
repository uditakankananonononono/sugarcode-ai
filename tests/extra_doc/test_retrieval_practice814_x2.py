import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.retrieval_practice814_x2 import compare_answer_tokens as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 'x', 'x'), ('b', 'y', 'z')]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^answers: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^answers: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'answers: row count outside declared range'),([None]*33,'answers: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'answers: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'answer labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))


@pytest.mark.parametrize('slot',[1,2])
@pytest.mark.parametrize('bad,error,msg',[(S('x'),TypeError,'answer tokens must be exact strings'),(0,TypeError,'answer tokens must be exact strings'),(None,TypeError,'answer tokens must be exact strings'),('x'*25,ValueError,'answer tokens must be 0..24 ASCII word characters'),('é',ValueError,'answer tokens must be 0..24 ASCII word characters'),('a!',ValueError,'answer tokens must be 0..24 ASCII word characters')])
def test_token_slots(slot,bad,error,msg):
    row=list(ROWS[1]);row[slot]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],row])

def test_independent_token_oracle():
    for expected,answer in itertools.product(('','a','A','a_b','x'*24),repeat=2):
        equal=list(expected)==list(answer)
        assert run([('a',expected,answer)])=={'matched':['a'] if equal else [],'mismatched':[] if equal else ['a'],'score':F(int(equal)),'recall_evaluated':False}
    rows=[('q_'+str(i).zfill(2),'a','a' if i%2 else 'b') for i in reversed(range(32))];result=run(rows)
    assert result['matched']==sorted(r[0] for r in rows if r[2]=='a') and result['mismatched']==sorted(r[0] for r in rows if r[2]=='b') and result['score']==F(1,2)
    from sugarcode.extra_doc import retrieval_practice814_x2 as m
    assert 'NOT_CLAIMED: actual recall, semantic correctness, question validity, learning' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^answer labels must be unique$'):run([('a','x','x'),('a','y','z')])
    assert run([('a','x','x'),('b','x','x')])['score']==1

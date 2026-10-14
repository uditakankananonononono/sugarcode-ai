import copy
import random
import string

import pytest
from sugarcode.extra_doc import health_quiz1191 as m

SCOPE = 'PARTIAL: supplied quiz-key comparison only; no health-content judgment'
NC = ['does not generate health advice or educational content',
      'does not validate the supplied answer key',
      'does not measure health literacy or clinical knowledge',
      'does not establish learning or health outcomes']


def oracle(key, responses):
    # Reverse scan for last occurrence, no nested update map.
    learners = sorted({r[0] for r in responses})
    scores = []
    for learner in learners:
        selected = []
        for q, expected in key:
            found = next((r[2] for r in reversed(responses) if r[:2] == (learner, q) or tuple(r[:2]) == (learner, q)), None)
            if found is not None:
                selected.append(found == expected)
        scores.append((learner, sum(selected), len(selected), len(key)-len(selected)))
    return dict(scores=scores, scope=SCOPE, not_claimed=NC)


def test_known_and_pins():
    key = [('q','a'),['r','b']]
    rows = [('z','q','a'),['z','q','A'],('b','q','a'),('z','r','b')]
    before = copy.deepcopy((key,rows))
    out = m.score_quiz(key, rows)
    assert out == dict(scores=[('b',1,1,1),('z',1,2,0)],scope=SCOPE,not_claimed=NC)
    assert (key,rows) == before
    out['scores'].append(('fake',0,0,0));out['not_claimed'][0]+='x'
    assert m.score_quiz(key,rows) == oracle(key,rows)
    assert m.score_quiz(key,[]) == oracle(key,[])
    assert m.SCOPE == SCOPE and m.NOT_CLAIMED == tuple(NC)
    assert m.__doc__.split('\n\n')[1] == ('PARTIAL: caller-supplied quiz response scoring only. No health information is\n'
        'created or validated; no health literacy, clinical knowledge or outcome claim.')


def test_oracle():
    rng = random.Random(1191)
    for _ in range(500):
        key = [('q'+str(i),rng.choice('Ab_1')) for i in range(rng.randrange(1,33))]
        rows = [(rng.choice(['a','b','_', '0','X']),rng.choice(key)[0],rng.choice('Ab_1')) for _ in range(rng.randrange(65))]
        assert m.score_quiz(tuple(key), tuple(rows)) == oracle(key,rows)


class L(list): pass
class T(tuple): pass
class S(str): pass


def bad(exc, msg, key, rows):
    with pytest.raises(exc) as e: m.score_quiz(key,rows)
    assert str(e.value) == msg


def test_containers_counts_precedence():
    key = [('q','a')]
    for x in (None, {}, 'qa', L(key), T(key)):
        bad(TypeError,'key must be an exact list or tuple',x,[])
    for x in ([],[None]*33):bad(ValueError,'key must contain 1..32 questions',x,None)
    for x in (None, {}, 'qa', L(['q','a']), T(('q','a'))):
        bad(TypeError,'key row must be an exact list or tuple',[x],None)
    for x in ([],['q'],['q','a','b']):bad(ValueError,'key row must have two identifiers',[x],None)
    bad(ValueError,'key question identifiers must be unique',[('q','a'),('q','b')],None)
    for x in (None, {}, 'qa', L([]), T(())):
        bad(TypeError,'responses must be an exact list or tuple',key,x)
    bad(ValueError,'at most 64 responses required',key,[None]*65)
    for x in (None, {}, 'qa', L(['l','q','a']), T(('l','q','a'))):
        bad(TypeError,'response row must be an exact list or tuple',key,[x])
    for x in ([],['l'],['l','q'],['l','q','a','b']):
        bad(ValueError,'response row must have three identifiers',key,[x])
    bad(ValueError,'response question must occur in key',key,[('l','x','a')])
    bad(ValueError,'at most 16 learners allowed',key,[(str(i),'q','a') for i in range(17)])
    k=[('q'+str(i),'a') for i in range(32)];rows=[(str(i),'q0','a') for i in range(16)]*4
    assert m.score_quiz(k,rows)==oracle(k,rows)
    bad(TypeError,'identifier must be an exact string',key,[(str(i),'q','a') for i in range(17)]+[('z','q',None)])


def test_labels_every_position():
    positions=[(0,0),(0,1),(1,0),(1,1),(1,2)]
    for which,idx in positions:
        for x in (None,1,True,b'a',S('a')):
            k=[['q','a']];r=[['l','q','a']];(k if which==0 else r)[0][idx]=x
            bad(TypeError,'identifier must be an exact string',k,r)
        for x in ('','a'*25,'É','Α','Ａ','🙂','a\n','a b'):
            k=[['q','a']];r=[['l','q','a']];(k if which==0 else r)[0][idx]=x
            bad(ValueError,'identifier must be 1..24 ASCII word characters',k,r)
    for c in string.printable+'éΑＡЖ🙂\u200b\x00':
        if c in string.ascii_letters+string.digits+'_':
            assert m.score_quiz([(c,'a')],[(c,c,'a')])['scores']==[(c,1,1,0)]
        else:bad(ValueError,'identifier must be 1..24 ASCII word characters',[(c,'a')],[])
    assert m.score_quiz([('q'*24,'a'*24)],[('l'*24,'q'*24,'a'*24)])['scores']==[('l'*24,1,1,0)]

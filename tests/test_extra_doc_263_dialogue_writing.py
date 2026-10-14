import pytest
from sugarcode.extra_doc.dialogue_writing import generate_dialogue as solve

RULES=[('A','Can you help?','start','asked'),('A','I can do it myself.','start','alone'),
       ('B','Yes. What is wrong?','asked','accepted'),('A','The door is locked.','accepted','explained'),
       ('B','I have a key.','explained','resolved')]


def test_shortest_alternating_exchange_with_explicit_preconditions():
    r=solve(['A','B'],RULES,['start'],'resolved')
    assert [t['utterance'] for t in r['turns']]==['Can you help?','Yes. What is wrong?','The door is locked.','I have a key.']
    assert [t['speaker'] for t in r['turns']]==['A','B','A','B']
    assert r['turn_count']==4 and r['final_facts']==['accepted','asked','explained','resolved','start']
    assert not r['naturalness_claimed']


def test_shortest_path_not_first_depth_first_and_zero_turn():
    rules=RULES+[('A','Open sesame.','start','resolved')]
    assert solve(['A','B'],rules,['start'],'resolved')['turn_count']==1
    assert solve(['A','B'],RULES,['resolved'],'resolved',0)['turns']==[]
    with pytest.raises(ValueError,match='^no alternating dialogue reaches target within turn cap$'):
        solve(['A','B'],RULES,['start'],'resolved',3)


def test_same_speaker_cannot_continue_and_cycle_terminates():
    with pytest.raises(ValueError,match='^no alternating dialogue reaches target within turn cap$'):
        solve(['A','B'],[('A','one','start','next'),('A','two','next','end')],['start'],'end')
    with pytest.raises(ValueError,match='^no alternating dialogue reaches target within turn cap$'):
        solve(['A','B'],[('A','one','start','start'),('B','two','start','start')],['start'],'end')

@pytest.mark.parametrize('args,error,message',[
 ((None,RULES,[],'x'),TypeError,'speakers rules and facts must be lists or tuples'),
 ((['A'],RULES,[],'x'),ValueError,'exactly two speakers required'),
 ((['A','B'],[None]*33,[],'x'),ValueError,'rule count must be between 1 and 32'),
 ((['A','B'],RULES,[None]*33,'x'),ValueError,'initial fact count must not exceed 32'),
 ((['A','B'],RULES,[],'x',True),ValueError,'max_turns must be a nonbool integer between 0 and 8'),
 ((['A','B'],[('A','x')],[],'x'),ValueError,'speech rules must have four fields'),
 ((['A','A'],RULES,[],'x'),ValueError,'speakers must be distinct'),
 ((['A','B'],[('C','x','a','b')],[],'x'),ValueError,'rule speaker must be known'),
 ((['A','B'],RULES,[] ,True),TypeError,'labels must be strings'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_breadth_first_prefers_early_short_path_over_later_long_path():
    rules=[('A','ask','start','asked'),('A','detour','start','detour'),
           ('B','answer','asked','end'),('B','delay','detour','waiting'),
           ('A','again','waiting','ready'),('B','finally','ready','end')]
    assert [t['utterance'] for t in solve(['A','B'],rules,['start'],'end')['turns']]==['ask','answer']


def test_initial_noop_turn_must_enable_second_speaker():
    r=solve(['A','B'],[('A','hello','start','start'),('B','done','start','end')],['start'],'end')
    assert [t['speaker'] for t in r['turns']]==['A','B']


def test_initial_fact_count_32_admitted():
    assert solve(['A','B'],RULES,['resolved']+[str(i) for i in range(31)],'resolved')['turn_count']==0

@pytest.mark.parametrize('args,message',[
 ((['A','B'],RULES,[],''),'label length must be between 1 and 160'),
 ((['A','B'],RULES,[],'x'*161),'label length must be between 1 and 160'),
 ((['A','B'],RULES,[],' '),'labels must not be blank'),
 ((['A','B'],[],[],'x'),'rule count must be between 1 and 32'),
 ((['A','B'],RULES,[],'x',9),'max_turns must be a nonbool integer between 0 and 8'),
])
def test_remaining_boundary_errors(args,message):
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('expansions',[4096,4097])
def test_expanded_state_guard_exact_threshold_isolated(monkeypatch,expansions):
    # Isolate expansion accounting with a bounded queue fixture. No claim that
    # these repeated synthetic states occur in a real BFS or bound memory.
    import sugarcode.extra_doc.dialogue_writing as module
    class Queue:
        def __init__(self,entries):self.remaining=expansions
        def __bool__(self):return self.remaining>0
        def popleft(self):
            self.remaining-=1
            return frozenset({'start'}),0,[]
        def append(self,item):raise AssertionError('rule precondition is absent')
    monkeypatch.setattr(module,'deque',Queue)
    expected=('no alternating dialogue reaches target within turn cap' if expansions==4096
              else 'dialogue search exceeds 4096 expanded states')
    with pytest.raises(ValueError) as exc:
        solve(['A','B'],[('A','say','absent','end')],['start'],'end')
    assert str(exc.value)==expected

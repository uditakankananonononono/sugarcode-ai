import pytest
from sugarcode.extra_doc.interactive_art import simulate_installation as solve


def test_responsive_state_machine_explicit_trace_and_unmatched_event():
    rules=[('idle','touch','lit','blue'),('lit','touch','lit','pulse'),('lit','leave','idle','dark')]
    r=solve(['idle','lit'],rules,'idle',['unknown','touch','touch','leave','leave'])
    assert r['final_state']=='idle' and r['outputs']==['blue','pulse','dark']
    assert [t['after'] for t in r['trace']]==['idle','lit','lit','idle','idle']
    assert [t['before'] for t in r['trace']]==['idle','idle','lit','lit','idle']
    assert [t['output'] for t in r['trace']]==[None,'blue','pulse','dark',None]
    assert [t['event_index'] for t in r['trace']]==list(range(5))
    assert r['physical_execution_performed'] is False


def test_zero_events_max_shapes_and_label_boundary():
    assert solve(['x'],[],'x',[])['outputs']==[]
    states=[str(i) for i in range(16)];rules=[('0',str(i),'0','x') for i in range(64)]
    r=solve(states,rules,'0',['0']*256)
    assert len(r['outputs'])==256
    label='x'*80
    assert solve([label],[],label,[])['final_state']==label

@pytest.mark.parametrize('args,error,message',[
 ((None,[],'x',[]),TypeError,'states rules and events must be lists or tuples'),
 (([],[],'x',[]),ValueError,'state count must be between 1 and 16'),
 (([None]*17,[],'x',[]),ValueError,'state count must be between 1 and 16'),
 ((['x'],[None]*65,'x',[]),ValueError,'rule count must not exceed 64'),
 ((['x'],[],'x',[None]*257),ValueError,'event count must not exceed 256'),
 ((['x'],[None],'x',[]),ValueError,'rules must contain state event next_state output'),
 ((['x','x'],[],'x',[]),ValueError,'states must be unique'),
 ((['x'],[],'y',[]),ValueError,'initial state must be known'),
 ((['x'],[('x','e','y','o')],'x',[]),ValueError,'rule states must be known'),
 ((['x'],[('x','e','x','o')]*2,'x',[]),ValueError,'state event pairs must be unique'),
 (([True],[],'x',[]),TypeError,'labels must be strings'),
 (([''],[],'',[]),ValueError,'label length must be between 1 and 80'),
 ((['x'*81],[],'x',[]),ValueError,'label length must be between 1 and 80'),
 (([' '],[],' ',[]),ValueError,'labels must not be blank'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

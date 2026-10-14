from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.bandit_algorithms import epsilon_greedy_replay as solve


def test_initialization_exploration_exploitation_empirical_oracle():
    r=solve(2,[0,0,F(1,4),F(1,2),0],[F(1,4),F(3,4),1,0,1],F(1,2))
    assert [t['arm'] for t in r['trace']]==[0,1,1,1,0]
    assert [t['mode'] for t in r['trace']]==['initialize','initialize','explore','exploit','explore']
    assert r['counts']==[2,3] and r['reward_totals']==[F(5,4),F(7,4)]
    assert r['means']==[F(5,8),F(7,12)] and r['total_reward']==3
    assert r['trace'][3]['means_before']==[F(1,4),F(7,8)]
    assert r['regret_guarantee_claimed'] is False


def test_exploit_tie_first_arm_zero_and_full_epsilon():
    assert [t['arm'] for t in solve(2,[0,0,0],[1,1,0],0)['trace']]==[0,1,0]
    r=solve(3,[0,0,0,F(2,3)],[0,0,0,1],1)
    assert r['trace'][-1]['arm']==2 and r['trace'][-1]['mode']=='explore'
    assert solve(3,[0],[1])['means']==[1,None,None]
    assert solve(16,[0]*256,[0]*256)['total_reward']==0

@pytest.mark.parametrize('args,error,message',[
 ((True,[0],[0]),ValueError,'arm_count must be a nonbool integer between 1 and 16'),
 ((17,[None],[None]),ValueError,'arm_count must be a nonbool integer between 1 and 16'),
 ((1,None,[0]),TypeError,'tickets and rewards must be lists or tuples'),
 ((1,[],[]),ValueError,'round count must be between 1 and 256'),
 ((1,[None]*257,[None]*257),ValueError,'round count must be between 1 and 256'),
 ((1,[0],[]),ValueError,'tickets and rewards must have equal length'),
 ((1,[True],[0]),TypeError,'values must be nonbool int or Fraction'),
 ((1,[0],[1.0]),TypeError,'values must be nonbool int or Fraction'),
 ((1,[F(1,2**32)],[0]),ValueError,'rational values must fit 32 bits'),
 ((1,[0],[0],-1),ValueError,'epsilon must be between zero and one'),
 ((1,[1],[0]),ValueError,'tickets must be at least zero and less than one'),
 ((1,[-1],[0]),ValueError,'tickets must be at least zero and less than one'),
 ((1,[0],[-1]),ValueError,'rewards must be between zero and one'),
 ((1,[0],[2]),ValueError,'rewards must be between zero and one'),
])
def test_exact_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

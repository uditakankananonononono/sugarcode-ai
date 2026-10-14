import pytest
from sugarcode.extra_doc.toy_design import sliding_toy as solve


def test_scramble_board_and_shortest_solution_oracle():
    r=solve(['up','left','down'])
    assert r['board']==[3,1,0,2]
    assert r['solution_moves']==['up','right','down'] and r['solution_length']==3
    assert r['toy_safety_validated'] is False
    # Manhattan lower bound=3,and suppliedsolution3 provesoptimality.
    board=r['board'][:];goal=[1,2,3,0]
    assert sum(abs(i//2-goal.index(v)//2)+abs(i%2-goal.index(v)%2) for i,v in enumerate(board) if v)==3
    delta={'up':-2,'down':2,'left':-1,'right':1}
    for move in r['solution_moves']:
        i=board.index(0);j=i+delta[move];board[i],board[j]=board[j],board[i]
    assert board==goal and 1<=r['discovered_states']<=12


def test_solved_single_move_and_scramble_cap_admission():
    assert solve([])['solution_moves']==[]
    assert solve(['left'])['board']==[1,2,0,3]
    assert solve(['left'])['solution_moves']==['right']
    assert solve(['up','down']*16)['board']==[1,2,3,0]

@pytest.mark.parametrize('args,error,message',[
 ((None,),TypeError,'moves must be a list or tuple'),
 (([None]*33,),ValueError,'scramble count must not exceed 32'),
 (([True],),ValueError,'moves must be up down left or right strings'),
 ((['jump'],),ValueError,'moves must be up down left or right strings'),
 ((['right'],),ValueError,'scramble move leaves puzzle bounds'),
 ((['down'],),ValueError,'scramble move leaves puzzle bounds'),
 ((['up','up'],),ValueError,'scramble move leaves puzzle bounds'),
 ((['left','left'],),ValueError,'scramble move leaves puzzle bounds'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

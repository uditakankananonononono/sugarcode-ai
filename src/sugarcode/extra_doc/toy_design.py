"""Row 334 Toy Design: bounded sliding-puzzle play construction and solution.

Creates a 2x2 sliding puzzle by executing supplied legal blank moves from a
solved board, then finds a shortest solution using exhaustive BFS over at most
24 permutations. Returns the puzzle, solution moves and reachable-state count.
NOT_CLAIMED: toy safety, age suitability, engagement validation, physical
manufacturing, arbitrary puzzle size or autonomous publication.
"""
from collections import deque


def sliding_toy(scramble_moves):
    if type(scramble_moves) not in (list,tuple):raise TypeError('moves must be a list or tuple')
    if len(scramble_moves)>32:raise ValueError('scramble count must not exceed 32')
    if any(type(m) is not str or m not in ('up','down','left','right') for m in scramble_moves):
        raise ValueError('moves must be up down left or right strings')
    deltas={'up':(-1,0),'down':(1,0),'left':(0,-1),'right':(0,1)}
    def step(board,move):
        index=board.index(0);y,x=divmod(index,2);dy,dx=deltas[move];ny=y+dy;nx=x+dx
        if not 0<=ny<2 or not 0<=nx<2:return None
        target=2*ny+nx;result=list(board);result[index],result[target]=result[target],result[index]
        return tuple(result)
    goal=(1,2,3,0);board=goal
    for move in scramble_moves:
        next_board=step(board,move)
        if next_board is None:raise ValueError('scramble move leaves puzzle bounds')
        board=next_board
    queue=deque([(board,[])]);seen={board}
    while queue:
        current,path=queue.popleft()
        if current==goal:
            return {'board':list(board),'solution_moves':path,'solution_length':len(path),
                    'discovered_states':len(seen),'toy_safety_validated':False}
        for move in deltas:
            nxt=step(current,move)
            if nxt is None or nxt in seen:continue
            seen.add(nxt);queue.append((nxt,path+[move]))
    raise ValueError('generated puzzle has no solution')

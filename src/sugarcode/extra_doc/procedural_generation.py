"""Row 300 Procedural Generation: deterministic perfect grid-maze generation.

Builds a spanning tree of orthogonal grid cells using depth-first traversal
and a supplied permutation of four direction codes. Generates connected,
cycle-free passages with an explicit visitation order, no random state.
NOT_CLAIMED: artistic level quality, randomness, difficulty validation,
rendered gameplay, arbitrary geometry or deployment.
"""


def generate_maze(width,height,directions=(0,1,2,3)):
    for dimension in (width,height):
        if type(dimension) is not int or not 1<=dimension<=16:
            raise ValueError('dimensions must be nonbool integers between 1 and 16')
    if type(directions) not in (list,tuple) or len(directions)!=4:
        raise ValueError('directions must contain four direction codes')
    if any(type(d) is not int for d in directions) or set(directions)!={0,1,2,3}:
        raise ValueError('directions must be a permutation of nonbool codes zero through three')
    offsets=((1,0),(0,1),(-1,0),(0,-1));seen={(0,0)};stack=[(0,0)];order=[(0,0)];passages=[]
    while stack:
        x,y=stack[-1];next_cell=None
        for code in directions:
            dx,dy=offsets[code];nx=x+dx;ny=y+dy
            if 0<=nx<width and 0<=ny<height and (nx,ny) not in seen:
                next_cell=(nx,ny);break
        if next_cell is None:stack.pop();continue
        seen.add(next_cell);order.append(next_cell);passages.append(((x,y),next_cell));stack.append(next_cell)
    return {'width':width,'height':height,'passages':passages,'visit_order':order,
            'cell_count':width*height,'difficulty_validated':False}

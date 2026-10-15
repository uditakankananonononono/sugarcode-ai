"""Fractal Geometry (canonical2013): PARTIAL caller finite ternary mask refinement.

mask exacttuple9 exactintbits0/1,rowmajor3x3;depth exactint0..3. Startoneoccupied
cell;eachoccupiedcellreplacedby3x3mask,unoccupiedbyzeros. Returntupleofbinary
rowtuples,occupiedcount,nonemptyalignedboxcounts forboxsides1,3,...3^depth.
Depth0grid((1,),)regardlessmask;allzeromaskdepth>0empty. NoHausdorffdimension,
infinitefractal/naturalgeometryclaim. Validatemaskouter/cells,depthlast.
"""
SCOPE='PARTIAL: caller finite ternary self-similar mask grid and aligned box counts'
NOT_CLAIMED=('Hausdorff dimension','infinite fractal','natural geometry')


def refine(mask,depth):
    if type(mask) is not tuple or len(mask)!=9:raise ValueError('mask exact tuple9')
    for v in mask:
        if type(v) is not int or v not in (0,1):raise ValueError('mask exact bits')
    if type(depth) is not int or not 0<=depth<=3:raise ValueError('depth exact int0..3')
    grid=[[1]]
    for step in range(depth):
        n=len(grid);grid=[[grid[r//3][c//3]*mask[3*(r%3)+c%3] for c in range(n*3)] for r in range(n*3)]
    counts=[];n=len(grid)
    for level in range(depth+1):
        side=3**level;counts.append(sum(any(grid[r][c] for r in range(a,a+side) for c in range(b,b+side)) for a in range(0,n,side) for b in range(0,n,side)))
    return {'grid':tuple(tuple(row) for row in grid),'occupied':sum(map(sum,grid)),'box_counts':tuple(counts),'geometry_validated':False}

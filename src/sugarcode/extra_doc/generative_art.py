"""Row 315 Generative Art: bounded integer cellular-automaton visual generation.

Creates binary raster art from a supplied elementary rule (0..255) and seed
row, using a periodic horizontal boundary. Produces an SVG image and exact
binary rows. This is generated visual content, not a diagnostic.
NOT_CLAIMED: artistic originality, aesthetic quality, arbitrary media,
interactive display or autonomous publication.
"""


def cellular_art(seed,rule,rows):
    if type(seed) not in (list,tuple):raise TypeError('seed must be a list or tuple')
    if not 1<=len(seed)<=128:raise ValueError('seed width must be between 1 and 128')
    if type(rule) is not int or not 0<=rule<=255:raise ValueError('rule must be a nonbool integer zero through 255')
    if type(rows) is not int or not 1<=rows<=128:raise ValueError('rows must be a nonbool integer between 1 and 128')
    if any(type(v) is not int or v not in (0,1) for v in seed):raise ValueError('seed values must be nonbool binary integers')
    width=len(seed);grid=[list(seed)]
    for y in range(1,rows):
        prior=grid[-1];next_row=[]
        for x in range(width):
            code=4*prior[(x-1)%width]+2*prior[x]+prior[(x+1)%width]
            next_row.append((rule>>code)&1)
        grid.append(next_row)
    rectangles=[]
    for y,row in enumerate(grid):
        for x,v in enumerate(row):
            if v:rectangles.append(f'<rect x="{x}" y="{y}" width="1" height="1"/>')
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {rows}" shape-rendering="crispEdges"><rect width="100%" height="100%" fill="white"/><g fill="black">'+''.join(rectangles)+'</g></svg>'
    return {'grid':grid,'svg':svg,'live_cell_count':sum(sum(row) for row in grid),'artistic_quality_validated':False}

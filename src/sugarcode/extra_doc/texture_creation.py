"""Row 292 Texture Creation: bounded procedural RGB checker surface.

Generates a digital surface map from two supplied 8-bit RGB colors and a
checker tile size. Alternates exact rectangular tiles, optionally flips
phase; edges are clipped to requested dimensions. Output is raw RGB pixels.
NOT_CLAIMED: photorealistic materials, physical shading, artistic originality,
seamless tiling for arbitrary dimensions, surface UV mapping or deployment.
"""


def checker_texture(width,height,color_a,color_b,tile_size=8,phase=0):
    for dimension in (width,height):
        if type(dimension) is not int or not 1<=dimension<=128:
            raise ValueError('dimensions must be nonbool integers between 1 and 128')
    if type(tile_size) is not int or not 1<=tile_size<=128:
        raise ValueError('tile_size must be a nonbool integer between 1 and 128')
    if type(phase) is not int or phase not in (0,1):
        raise ValueError('phase must be a nonbool integer zero or one')
    for color in (color_a,color_b):
        if type(color) not in (list,tuple) or len(color)!=3:
            raise ValueError('colors must be RGB lists or tuples')
    if any(type(c) is not int or not 0<=c<=255 for color in (color_a,color_b) for c in color):
        raise ValueError('channels must be nonbool integers between zero and 255')
    pixels=[];counts=[0,0]
    for y in range(height):
        row=[]
        for x in range(width):
            index=(x//tile_size+y//tile_size+phase)%2
            row.append(list(color_a if index==0 else color_b));counts[index]+=1
        pixels.append(row)
    return {'pixels':pixels,'color_counts':counts,'width':width,'height':height,'photorealism_claimed':False}

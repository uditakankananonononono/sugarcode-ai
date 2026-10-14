"""Row 327, Textile Design: exact repeat-tile geometry for a fabric pattern.

A pattern is a tile of tile_w x tile_h cells and a list of motifs (x, y, w, h, ch): a filled
rectangle of the character ch whose top-left cell is (x, y). A motif that runs past the
right or bottom edge wraps round to the other side, so the tile repeats without a seam.
build_repeat returns, exactly:
- tile: the tile as text rows ('.' empty, the motif character where exactly one motif covers
  a cell, '*' where two or more motifs overlap);
- overlap_cells and covered_cells (counts) and coverage (covered / all cells, a Fraction);
- swatch: two tiles side by side where the second is dropped by `drop` rows (a "drop repeat":
  row r of the second tile is row (r - drop) mod tile_h of the first);
- fabric: for a bolt of width fabric_w and length fabric_l (cells), how many whole repeats
  fit across and down, the leftover cells, and the repeats needed to cover the cloth
  (ceiling).
Caps: tile 1 to 32 cells each way, 1 to 16 motifs, motif sizes 1 to the tile size, x and y inside the
tile, ch one printable non-space ASCII character other than '.' and '*', drop 0 to tile_h - 1,
fabric 1 to 1000 cells. All numbers are nonbool int. Order of checks: tile size, motif list (in
order: structure, then values), drop, fabric, and only then any rendering.

NOT_CLAIMED: geometry only. It does not judge whether a pattern is attractive, printable, on trend or
weavable; no colour, thread count, shrinkage, dye, repeat-match rules of a mill, or rendering to an
image. No clinical or wet-lab claim.
"""

from fractions import Fraction

MAX_TILE, MAX_MOTIFS, MAX_FABRIC = 32, 16, 1000


def _int(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be a nonbool int')


def build_repeat(tile_w, tile_h, motifs, drop, fabric_w, fabric_l):
    _int(tile_w, 'tile_w')
    _int(tile_h, 'tile_h')
    if not 1 <= tile_w <= MAX_TILE or not 1 <= tile_h <= MAX_TILE:
        raise ValueError('tile size must be between 1 and 32 cells each way')
    if type(motifs) not in (list, tuple):
        raise TypeError('motifs must be a list or tuple')
    if not 1 <= len(motifs) <= MAX_MOTIFS:
        raise ValueError('motif count must be between 1 and 16')
    for m in motifs:
        if type(m) not in (list, tuple) or len(m) != 5:
            raise TypeError('each motif must be (x, y, w, h, ch)')
        for v, nm in zip(m[:4], 'xywh'):
            _int(v, 'motif ' + nm)
        if type(m[4]) is not str:
            raise TypeError('motif ch must be str')
        x, y, w, h, ch = m
        if not 0 <= x < tile_w or not 0 <= y < tile_h:
            raise ValueError('motif origin must lie inside the tile')
        if not 1 <= w <= tile_w or not 1 <= h <= tile_h:
            raise ValueError('motif size must be between 1 and the tile size')
        if len(ch) != 1 or not 33 <= ord(ch) <= 126 or ch in '.*':
            raise ValueError("motif ch must be one printable non-space character other than '.' and '*'")
    _int(drop, 'drop')
    if not 0 <= drop < tile_h:
        raise ValueError('drop must be between 0 and tile_h - 1')
    _int(fabric_w, 'fabric_w')
    _int(fabric_l, 'fabric_l')
    if not 1 <= fabric_w <= MAX_FABRIC or not 1 <= fabric_l <= MAX_FABRIC:
        raise ValueError('fabric size must be between 1 and 1000 cells')
    owners = [[[] for _ in range(tile_w)] for _ in range(tile_h)]
    for i, (x, y, w, h, ch) in enumerate(motifs):
        for dy in range(h):
            for dx in range(w):
                owners[(y + dy) % tile_h][(x + dx) % tile_w].append(i)
    rows, over, cov = [], 0, 0
    for r in range(tile_h):
        row = ''
        for c in range(tile_w):
            o = owners[r][c]
            if not o:
                row += '.'
            elif len(o) == 1:
                row += motifs[o[0]][4]
                cov += 1
            else:
                row += '*'
                over += 1
                cov += 1
        rows.append(row)
    swatch = [rows[r] + rows[(r - drop) % tile_h] for r in range(tile_h)]
    return {'tile': rows, 'overlap_cells': over, 'covered_cells': cov,
            'coverage': Fraction(cov, tile_w * tile_h), 'swatch': swatch,
            'fabric': {'across': fabric_w // tile_w, 'down': fabric_l // tile_h,
                       'leftover_width': fabric_w % tile_w, 'leftover_length': fabric_l % tile_h,
                       'repeats_to_cover': ((fabric_w + tile_w - 1) // tile_w) * ((fabric_l + tile_h - 1) // tile_h)}}

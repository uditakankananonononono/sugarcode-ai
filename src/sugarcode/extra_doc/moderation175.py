"""Row175 Moderation Analysis: PARTIAL binary-moderator linear interaction.

rows exact list4..8 exact (X,Z,Y) tuples. X and Y exact ints-5..5; Z exact
int0..1. Each moderator group must contain distinct X values. Fit independent
OLS Y=intercept_z+slope_z*X. Reconstruct coefficients (b0,bX,bZ,bXZ) for
Y=b0+bX*X+bZ*Z+bXZ*X*Z. Crossover is X where the two fitted lines meet,
None for equal slopes (even if lines coincide). Return exact residual SSE.
Validation: outer, each shape/X/Z/Y before next row, group0 variation then
 group1 variation after all scalar checks. No causal or inferential claims.
"""
from fractions import Fraction as F
SCOPE = 'PARTIAL: exact binary-moderator OLS slope heterogeneity and line crossover'
NOT_CLAIMED = ('causal moderation', 'significance testing', 'continuous moderators',
               'measurement validity', 'sampling uncertainty')


def fit(rows):
    if type(rows) is not list or not 4 <= len(rows) <= 8:
        raise ValueError('rows must be exact list4..8')
    for row in rows:
        if type(row) is not tuple or len(row) != 3:
            raise ValueError('row must be exact X Z Y triple tuple')
        for j, name, low, high in ((0,'X',-5,5),(1,'Z',0,1),(2,'Y',-5,5)):
            if type(row[j]) is not int or not low <= row[j] <= high:
                raise ValueError(name + ' must be exact int' + str(low) + '..' + str(high))
    lines = []
    for z in (0,1):
        group = [(x,y) for x,g,y in rows if g == z]
        n = len(group)
        sx = sum(x for x,y in group)
        sy = sum(y for x,y in group)
        sxx = sum(x*x for x,y in group)
        sxy = sum(x*y for x,y in group)
        den = n*sxx-sx*sx
        if not den:
            raise ValueError('group' + str(z) + ' must contain distinct X values')
        slope = F(n*sxy-sx*sy, den)
        lines.append((F(sy-slope*sx,n), slope))
    a0,b0 = lines[0]
    a1,b1 = lines[1]
    delta_a, delta_b = a1-a0,b1-b0
    sse = sum(((y-lines[z][0]-lines[z][1]*x)**2 for x,z,y in rows), F(0))
    return {'coefficients': (a0,b0,delta_a,delta_b), 'group_lines': lines,
            'crossover': -delta_a/delta_b if delta_b else None, 'sse': sse,
            'causal_moderation_identified': False}

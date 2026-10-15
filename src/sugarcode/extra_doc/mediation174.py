"""Row174 Mediation Analysis: PARTIAL exact linear single-mediator OLS decomposition.

rows exact list3..8 of exact (X,M,Y) tuples, exact integer values-5..5.
Fit M=alpha+aX; Y=beta+direct*X+b*M; Y=gamma+total*X by exact ordinary least
squares with intercepts. Require nonsingular design [1,X,M], otherwise error.
Return coefficients, indirect=a*b, and exact total-direct-indirect residual.
No causal/sequential ignorability, measurement validity, uncertainty, nonlinear
mediation or treatment advice claim. Duplicate observations remain weighted.
Validate collection, then each row shape and X/M/Y values before next row;
rank check follows every scalar validation. Pure linear-association decomposition.
"""
from fractions import Fraction as F
SCOPE = 'PARTIAL: exact supplied-data linear OLS single-mediator coefficient decomposition'
NOT_CLAIMED = ('causal mediation', 'sequential ignorability', 'measurement validity',
               'sampling uncertainty', 'nonlinear effects')


def decompose(rows):
    if type(rows) is not list or not 3 <= len(rows) <= 8:
        raise ValueError('rows must be exact list3..8')
    for row in rows:
        if type(row) is not tuple or len(row) != 3:
            raise ValueError('row must be exact X M Y triple tuple')
        for value in row:
            if type(value) is not int or not -5 <= value <= 5:
                raise ValueError('values must be exact ints-5..5')

    def fit(design, outcomes):
        p = len(design[0])
        system = [[F(sum(row[i]*row[j] for row in design)) for j in range(p)] +
                  [F(sum(row[i]*y for row,y in zip(design,outcomes)))] for i in range(p)]
        for k in range(p):
            pivot = next((i for i in range(k,p) if system[i][k]), None)
            if pivot is None:
                raise ValueError('intercept X M design must have full column rank')
            system[k], system[pivot] = system[pivot], system[k]
            scale = system[k][k]
            system[k] = [x/scale for x in system[k]]
            for i in range(p):
                if i != k:
                    scale = system[i][k]
                    system[i] = [x-scale*y for x,y in zip(system[i],system[k])]
        return tuple(row[-1] for row in system)
    yfit = fit([(1,x,med) for x,med,y in rows], [y for x,med,y in rows])
    mfit = fit([(1,x) for x,med,y in rows], [med for x,med,y in rows])
    total = fit([(1,x) for x,med,y in rows], [y for x,med,y in rows])
    indirect = mfit[1]*yfit[2]
    return {'mediator_fit': mfit, 'outcome_fit': yfit, 'total_fit': total,
            'indirect': indirect, 'direct': yfit[1],
            'decomposition_residual': total[1]-yfit[1]-indirect,
            'causal_mediation_identified': False}

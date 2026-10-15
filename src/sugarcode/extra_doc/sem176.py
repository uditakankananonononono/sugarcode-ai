"""Row176 Structural Equation Modeling: PARTIAL recursive linear implied covariance.

coefficients exact list1..4 exact tuple square rows, exact ints-2..2. Entry
B[i][j] is effect of variable j on i in X=B*X+epsilon; require zeros for j>=i.
variances exact tuple of n exact ints0..4 for independent zero-mean noises.
Return total effects A=(I-B)^-1, including diagonal1, and covariance A*V*A^T,
all exact Fraction cells in list-of-tuples format. No parameter fitting,
correlated noises, cycles, real causal meaning or model validity inferred.
Validation: matrix outer, variances shape, each row shape, each entry value
then upper/diagonal zero requirement before next entry; variances last.
"""
from fractions import Fraction as F
SCOPE = 'PARTIAL: exact recursive linear SEM total effects and implied covariance'
NOT_CLAIMED = ('parameter estimation', 'causal identification', 'model validity',
               'correlated errors', 'cyclic equations')


def imply(coefficients, variances):
    if type(coefficients) is not list or not 1 <= len(coefficients) <= 4:
        raise ValueError('coefficients must be exact list1..4')
    n = len(coefficients)
    if type(variances) is not tuple or len(variances) != n:
        raise ValueError('variances must be exact tuple of node count')
    for i, row in enumerate(coefficients):
        if type(row) is not tuple or len(row) != n:
            raise ValueError('coefficient row must be exact tuple of node count')
        for j, value in enumerate(row):
            if type(value) is not int or not -2 <= value <= 2:
                raise ValueError('coefficients must be exact ints-2..2')
            if j >= i and value != 0:
                raise ValueError('diagonal and upper coefficients must be zero')
    for value in variances:
        if type(value) is not int or not 0 <= value <= 4:
            raise ValueError('variances must be exact ints0..4')
    effects = [[F(int(i==j)) for j in range(n)] for i in range(n)]
    covariance = [[F(0) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for k in range(i):
            for j in range(n):
                effects[i][j] += coefficients[i][k]*effects[k][j]
        for j in range(i):
            covariance[i][j] = sum((coefficients[i][k]*covariance[k][j] for k in range(i)),F(0))
            covariance[j][i] = covariance[i][j]
        covariance[i][i] = F(variances[i]) + sum((coefficients[i][j]*coefficients[i][k]*covariance[j][k]
                                               for j in range(i) for k in range(i)),F(0))
    return {'total_effects': [tuple(row) for row in effects],
            'covariance': [tuple(row) for row in covariance], 'model_validated': False}

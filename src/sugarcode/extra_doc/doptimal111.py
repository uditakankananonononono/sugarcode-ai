"""Row 111 Experimental Design Optimization - Creates most efficient experiments to test hypotheses.

PARTIAL: exact subset D-optimality for supplied bounded two-parameter design rows.
Input exact dict rows and choose; rows is an exact list of 2..8 exact two-value
lists of exact integers -3..3. Choose is an exact integer 2..len(rows). For every
subset of choose distinct row positions, score det(sum x*x^T). Return indices
as the lexicographically first maximizing index list, determinant as an integer,
information as a two-by-two integer matrix, and claims as three False booleans.
Duplicate vectors are permitted distinct candidate positions; singular winners
are allowed with score zero. No intercept is added or model/noise validity checked.
NOT_CLAIMED: actual experiment efficiency, hypothesis validity, production readiness.
"""
from itertools import combinations
SCOPE = 'PARTIAL: exact finite two-parameter D-optimal subset selection only'
NOT_CLAIMED = ('actual experiment efficiency', 'hypothesis validity', 'production readiness')


def select(data):
    if type(data) is not dict or set(data) != {'rows', 'choose'}:
        raise ValueError('exact dict with rows and choose required')
    rows, choose = data['rows'], data['choose']
    if type(rows) is not list or not 2 <= len(rows) <= 8:
        raise ValueError('rows must be an exact list of 2..8 vectors')
    for row in rows:
        if type(row) is not list or len(row) != 2:
            raise ValueError('vectors must be exact two-value lists')
        for value in row:
            if type(value) is not int or not -3 <= value <= 3:
                raise ValueError('values must be exact integers -3..3')
    if type(choose) is not int or not 2 <= choose <= len(rows):
        raise ValueError('choose must be an exact integer 2..row count')
    best = -1
    indices = None
    information = None
    for subset in combinations(range(len(rows)), choose):
        a = sum(rows[i][0]**2 for i in subset)
        b = sum(rows[i][0]*rows[i][1] for i in subset)
        c = sum(rows[i][1]**2 for i in subset)
        determinant = a*c-b*b
        if determinant > best:
            best = determinant
            indices = list(subset)
            information = [[a, b], [b, c]]
    return {'indices': indices, 'determinant': best, 'information': information, 'claims': [False, False, False]}

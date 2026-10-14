"""Doc row1765 Game Theory: PARTIAL supplied two-player pure-strategy fixture.

Matrix exact list2..10 rows exact list2..10 uniform widths, cells exact tuples
(row_payoff,col_payoff) exact ints-1000..1000. Return all weak pure Nash indices
(zero-based) and each player's best responses including ties. No mixed strategy,
equilibrium selection, actual player behavior or economic validity.
"""


def pure_equilibria(matrix):
    if type(matrix) is not list or not 2<=len(matrix)<=10:raise ValueError('matrix must be an exact list with 2..10 rows')
    width=None
    for row in matrix:
        if type(row) is not list or not 2<=len(row)<=10:raise ValueError('rows must be exact lists with 2..10 cells')
        if width is None:width=len(row)
        if len(row)!=width:raise ValueError('matrix rows must have equal widths')
        for cell in row:
            if type(cell) is not tuple or len(cell)!=2:raise ValueError('cell must be a two-payoff tuple')
            if any(type(x) is not int or not -1000<=x<=1000 for x in cell):raise ValueError('payoffs must be exact integers in -1000..1000')
    row_best=[(j,[i for i in range(len(matrix)) if matrix[i][j][0]==max(row[j][0] for row in matrix)]) for j in range(width)]
    col_best=[(i,[j for j in range(width) if matrix[i][j][1]==max(p[1] for p in matrix[i])]) for i in range(len(matrix))]
    equilibria=[(i,j) for i in range(len(matrix)) for j in range(width) if i in row_best[j][1] and j in col_best[i][1]]
    return {'equilibria':equilibria,'row_best':row_best,'col_best':col_best,'claim':'PARTIAL','behavior_validated':False}

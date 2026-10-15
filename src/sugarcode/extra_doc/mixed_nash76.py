"""Row76 Nash Equilibrium Identification - Finds stable states in competitive situations.
PARTIAL: all mixed/pure Nash equilibria of nondegenerate supplied 2x2 game.
Exact dict row,column, each exact two-row list of exact two-item lists of exact
integer payoffs -5..5. Row payoff differences across its actions must be nonzero
for each column action; column payoff differences across its actions must be
nonzero for each row action. Return equilibria [row_action0_probability pair,
column_action0_probability pair] sorted lex by rational probabilities, and
claims3False. Strict endpoint best responses exclude continuum degeneracies;
interior solution calculated by exact indifference, not numerical iteration.
NOT_CLAIMED: real competitive stability, general game solver, production readiness.
"""
from fractions import Fraction
SCOPE='PARTIAL: exact nondegenerate supplied 2x2 complete Nash equilibria only'
NOT_CLAIMED=('real competitive stability','general game solver','production readiness')


def solve(data):
    if type(data) is not dict or set(data)!={'row','column'}:
        raise ValueError('exact dict with row and column required')
    a=data['row'];b=data['column']
    for matrix in (a,b):
        if type(matrix) is not list or len(matrix)!=2:
            raise ValueError('payoff matrix must be an exact two-row list')
        for row in matrix:
            if type(row) is not list or len(row)!=2:
                raise ValueError('payoff row must be an exact two-item list')
            for v in row:
                if type(v) is not int or not -5<=v<=5:
                    raise ValueError('payoffs must be exact integers -5..5')
    if any(a[0][j]==a[1][j] for j in range(2)) or any(b[i][0]==b[i][1] for i in range(2)):
        raise ValueError('strict endpoint payoff differences required')
    equilibria=[]
    for i in range(2):
        for j in range(2):
            if a[i][j]>a[1-i][j] and b[i][j]>b[i][1-j]:
                equilibria.append((Fraction(1-i),Fraction(1-j)))
    row_left=a[0][0]-a[1][0];row_right=a[0][1]-a[1][1]
    column_top=b[0][0]-b[0][1];column_bottom=b[1][0]-b[1][1]
    if row_left*row_right<0 and column_top*column_bottom<0:
        q=Fraction(-row_right,row_left-row_right)
        p=Fraction(-column_bottom,column_top-column_bottom)
        equilibria.append((p,q))
    return {'equilibria':[[[p.numerator,p.denominator],[q.numerator,q.denominator]] for p,q in sorted(equilibria)],'claims':[False,False,False]}

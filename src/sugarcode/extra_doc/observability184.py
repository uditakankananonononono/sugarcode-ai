"""Row184 State Space Models - exact finite-horizon two-state observability.
PARTIAL: exact dict matrix,sensor,horizon. Matrix exact list2 exact list2 rows
exact ints-2..2; sensor exact list2 exact ints-2..2; horizon exact int1..5.
Observation rows are sensor*A^k, k0..horizon-1. Return rows, Gramian O^T O,
rank, unobservable rational basis (canonical first free coordinate1), claims3False.
For rank0 standard coordinate basis; rank2 empty basis. No system fitted.
NOT_CLAIMED: identified real dynamics, noisy state estimation, production readiness.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: exact supplied two-state finite-horizon observability matrix and nullspace only'
NOT_CLAIMED=('identified real dynamics','noisy state estimation','production readiness')

def analyze(data):
    if type(data) is not dict or set(data)!={'matrix','sensor','horizon'}:raise ValueError('exact dict with matrix, sensor, horizon required')
    matrix=data['matrix'];sensor=data['sensor'];horizon=data['horizon']
    if type(matrix) is not list or len(matrix)!=2:raise ValueError('matrix must be an exact two-row list')
    for row in matrix:
        if type(row) is not list or len(row)!=2:raise ValueError('matrix row must be an exact two-item list')
        for v in row:
            if type(v) is not int or not -2<=v<=2:raise ValueError('matrix entries must be exact integers -2..2')
    if type(sensor) is not list or len(sensor)!=2:raise ValueError('sensor must be an exact two-item list')
    for v in sensor:
        if type(v) is not int or not -2<=v<=2:raise ValueError('sensor entries must be exact integers -2..2')
    if type(horizon) is not int or not 1<=horizon<=5:raise ValueError('horizon must be an exact integer 1..5')
    rows=[];row=sensor[:]
    for _ in range(horizon):
        rows.append(row);row=[sum(row[i]*matrix[i][j] for i in range(2)) for j in range(2)]
    gram=[[sum(row[i]*row[j] for row in rows) for j in range(2)] for i in range(2)]
    nonzero=[row for row in rows if any(row)]
    if not nonzero:rank=0;basis=[[F(1),F(0)],[F(0),F(1)]]
    elif gram[0][0]*gram[1][1]!=gram[0][1]**2:rank=2;basis=[]
    else:
        rank=1;a,b=nonzero[0];basis=[[-F(b,a),F(1)]] if a else [[F(1),F(0)]]
    def pair(v):return [v.numerator,v.denominator]
    return {'observations':rows,'gramian':gram,'rank':rank,'unobservable_basis':[[pair(v) for v in row] for row in basis],'claims':[False,False,False]}

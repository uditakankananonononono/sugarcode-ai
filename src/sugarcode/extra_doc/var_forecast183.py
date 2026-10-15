"""Row183 Vector Autoregression - exact supplied bivariate VAR(1) forecast.
PARTIAL: exact dict matrix,state,variances,horizon. Matrix exact list2 exact
list2 rows ints-2..2; state exact list2 ints-3..3; variances exact list2 ints0..3;
horizon exact int1..5. X_next=A*X+noise; independent innovation covariance is
supplied diagonal variances. Return mean and full forecast covariance at each
horizon, including initial known state/covariance0, claims3False. No fitting.
NOT_CLAIMED: fitted time series, stable dynamics, production readiness.
"""
SCOPE='PARTIAL: exact supplied bivariate VAR forecast means and covariance propagation only'
NOT_CLAIMED=('fitted time series','stable dynamics','production readiness')

def forecast(data):
    if type(data) is not dict or set(data)!={'matrix','state','variances','horizon'}:raise ValueError('exact dict with matrix, state, variances, horizon required')
    a=data['matrix']
    if type(a) is not list or len(a)!=2:raise ValueError('matrix must be an exact two-row list')
    for row in a:
        if type(row) is not list or len(row)!=2:raise ValueError('matrix row must be an exact two-item list')
        for v in row:
            if type(v) is not int or not -2<=v<=2:raise ValueError('matrix entries must be exact integers -2..2')
    for key,lo,hi in [('state',-3,3),('variances',0,3)]:
        row=data[key]
        if type(row) is not list or len(row)!=2:raise ValueError(key+' must be an exact two-item list')
        for v in row:
            if type(v) is not int or not lo<=v<=hi:raise ValueError(key+' has invalid exact integer value')
    h=data['horizon']
    if type(h) is not int or not 1<=h<=5:raise ValueError('horizon must be an exact integer 1..5')
    state=data['state'][:];cov=[[0,0],[0,0]];means=[state];covariances=[cov]
    for _ in range(h):
        state=[sum(a[i][j]*state[j] for j in range(2)) for i in range(2)]
        cov=[[sum(a[i][j]*cov[j][k]*a[l][k] for j in range(2) for k in range(2))+(data['variances'][i] if i==l else 0) for l in range(2)] for i in range(2)]
        means.append(state);covariances.append(cov)
    return {'means':means,'covariances':covariances,'claims':[False,False,False]}

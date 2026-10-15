"""Row57 Non-Linear Thinking - Models exponential, logarithmic, and power-law relationships.
PARTIAL: exact transformed-predictor least-squares model comparison. Exact dict
x,y. X exact list3..4 unique exact ints from1,2,4,8; y exact x-length list ints
-8..8. Candidate predictors in fixed tie order exponential2^x, logarithmic log2x,
square x^2, cube x^3. Fit y=intercept+slope*predictor by exact OLS, select smallest
residual squared sum then family order. Return family, coefficients[pair,pair],
predictions rational pairs, errors[family,SSE pair] in family order, claims3False.
No causal model, extrapolation validation or general nonlinear reasoning.
NOT_CLAIMED: general nonlinear thinking, predictive validity, production readiness.
"""
from fractions import Fraction
SCOPE='PARTIAL: exact supplied four-family transformed-predictor OLS selection only'
NOT_CLAIMED=('general nonlinear thinking','predictive validity','production readiness')


def fit(data):
    if type(data) is not dict or set(data)!={'x','y'}:
        raise ValueError('exact dict with x and y required')
    x=data['x'];y=data['y']
    if type(x) is not list or not 3<=len(x)<=4:
        raise ValueError('x must be an exact list of 3..4 items')
    for v in x:
        if type(v) is not int or v not in (1,2,4,8):
            raise ValueError('x must contain exact integers from 1,2,4,8')
    if len(set(x))!=len(x):raise ValueError('x must be unique')
    if type(y) is not list or len(y)!=len(x):
        raise ValueError('y must be an exact x-length list')
    for v in y:
        if type(v) is not int or not -8<=v<=8:
            raise ValueError('y must contain exact integers -8..8')
    predictors=[('exponential',[2**v for v in x]),('logarithmic',[(1,2,4,8).index(v) for v in x]),('square',[v*v for v in x]),('cube',[v**3 for v in x])]
    models=[];n=len(x)
    for name,z in predictors:
        slope=Fraction(n*sum(a*b for a,b in zip(z,y))-sum(z)*sum(y),n*sum(v*v for v in z)-sum(z)**2)
        intercept=Fraction(sum(y),n)-slope*Fraction(sum(z),n)
        prediction=[intercept+slope*v for v in z]
        error=sum((a-b)**2 for a,b in zip(y,prediction))
        models.append((name,intercept,slope,prediction,error))
    index=min(range(len(models)),key=lambda i:(models[i][4],i));name,intercept,slope,prediction,_=models[index]
    def pair(v):return [v.numerator,v.denominator]
    return {'family':name,'coefficients':[pair(intercept),pair(slope)],'predictions':[pair(v) for v in prediction],'errors':[[row[0],pair(row[4])] for row in models],'claims':[False,False,False]}

"""Row 543: Machine Learning Pipeline - Automates ML workflow.

SCOPED planning aid over caller supplied rows. No external actions, persistence,
capability development evidence, organization quality, or optimal policy claim.
Explicit import only; 1..32 tuple rows. Labels are lowercase ASCII identifiers.
"""
import re

LABEL = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if len(value) > 24 or LABEL.fullmatch(value) is None:
        raise ValueError('label must be 1..24 lowercase identifier characters')


def _integer(value, low, high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low <= value <= high:
        raise ValueError('integer outside declared range')


def _rows(rows, arity):
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1 <= len(rows) <= 32:
        raise ValueError('row count must be 1..32')
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row) != arity:
            raise ValueError('wrong row arity')


def fit_evaluate(rows):
    """Rows: (sample_id, feature_int, target_int, training_bit 0/1).
    Exact one-feature ordinary least squares with intercept, fitted only on
    declared training rows and evaluated on held-out rows by exact MSE. One
    bounded in-memory workflow, no ML orchestration, registry or deployment.
    """
    _rows(rows, 4)
    for sample, feature, target, training in rows:
        _label(sample)
        _integer(feature, -1000, 1000)
        _integer(target, -1000, 1000)
        _integer(training, 0, 1)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate sample')
    train = [(feature,target) for _,feature,target,flag in rows if flag==1]
    evaluation = [(feature,target) for _,feature,target,flag in rows if flag==0]
    if len(train)<2 or not evaluation:
        raise ValueError('at least two training and one evaluation samples required')
    from fractions import Fraction as F
    n = len(train)
    sx = sum(x for x,_ in train)
    sy = sum(y for _,y in train)
    sxx = sum(x*x for x,_ in train)
    sxy = sum(x*y for x,y in train)
    denominator = n*sxx-sx*sx
    if denominator==0:
        raise ValueError('training feature variance must be positive')
    slope = F(n*sxy-sx*sy,denominator)
    intercept = F(sy,n)-slope*F(sx,n)
    predictions = [(sample,str(intercept+slope*feature)) for sample,feature,_,_ in sorted(rows)]
    mse = sum(((intercept+slope*x-y)**2 for x,y in evaluation),F(0))/len(evaluation)
    return {'slope_fraction':str(slope),'intercept_fraction':str(intercept),
            'predictions':predictions,'evaluation_mse_fraction':str(mse),
            'training_count':n,'evaluation_count':len(evaluation)}

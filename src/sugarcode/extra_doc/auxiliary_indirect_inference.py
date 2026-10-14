"""Row 1058 Indirect Inference - Simulation-based estimation.

Match an auxiliary mean/variance model on observed data against supplied
simulations.Observed exact integer list2..12 values-9..9;2..6 candidates
[label,simulated list] with2..12 integer values-9..9. Positive integer
mean and variance discrepancy weights1..9. Auxiliary variance is the
unbiased sample variance;zero variance allowed. Return observed auxiliary
moments,candidate moments and weighted squared differences;choose smallest
exact discrepancy,first supplied candidate on ties. ASCII labels1..8.
NOT_CLAIMED: simulator execution, parameter optimization, statistical
consistency guarantees, production readiness. Exact containers/caps.
"""
from fractions import Fraction
ALPHABET='abcdefghijklmnopqrstuvwxyz'
SCOPE='PARTIAL: finite-candidate auxiliary mean/variance matching only'
NOT_CLAIMED=('simulator execution','parameter optimization','statistical consistency guarantees','production readiness')


def _label(value):
    if type(value) is not str or not 1<=len(value)<=8 or any(c not in ALPHABET for c in value):
        raise ValueError('exact lowercase ASCII label required')


def _samples(values):
    if type(values) is not list or not 2<=len(values)<=12:
        raise ValueError('samples must be an exact list of 2..12 values')
    for value in values:
        if type(value) is not int or not -9<=value<=9:
            raise ValueError('samples must contain exact integers -9..9')


def _moments(values):
    mean=Fraction(sum(values),len(values))
    variance=sum((value-mean)**2 for value in values)/(len(values)-1)
    return mean,variance


def _pair(value):
    return [value.numerator,value.denominator]


def compare(data):
    if type(data) is not dict or set(data)!={'observed','candidates','weights'}:
        raise ValueError('exact dict with observed, candidates, weights required')
    observed,candidates,weights=(data[k] for k in ('observed','candidates','weights'))
    _samples(observed)
    if type(candidates) is not list or not 2<=len(candidates)<=6:
        raise ValueError('candidates must be an exact list of 2..6 records')
    if type(weights) is not list or len(weights)!=2:
        raise ValueError('weights must be an exact pair list')
    for weight in weights:
        if type(weight) is not int or not 1<=weight<=9:
            raise ValueError('weights must contain exact integers 1..9')
    seen=set()
    for record in candidates:
        if type(record) is not list or len(record)!=2:
            raise ValueError('candidate must be an exact pair list')
        label,samples=record
        _label(label)
        if label in seen:
            raise ValueError('candidate labels must be unique')
        seen.add(label)
        _samples(samples)
    observed_mean,observed_variance=_moments(observed)
    fitted={}
    best=None
    best_distance=None
    for label,samples in candidates:
        mean,variance=_moments(samples)
        distance=weights[0]*(mean-observed_mean)**2+weights[1]*(variance-observed_variance)**2
        fitted[label]={'mean':_pair(mean),'variance':_pair(variance),'distance':_pair(distance)}
        if best_distance is None or distance<best_distance:
            best=label
            best_distance=distance
    return {'observed':{'mean':_pair(observed_mean),'variance':_pair(observed_variance)},
            'fitted':fitted,'best':best,'claims':[False,False,False,False]}

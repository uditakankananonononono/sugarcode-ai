"""Row 1057 Synthetic Likelihood - Composite likelihood.

Fit a univariate Gaussian summary likelihood to supplied simulated summaries
for each parameter label.2..6 unique labels,each with2..12 integer summaries
-9..9;observed integer-9..9. Use unbiased sample variance (n-1),which must
be positive. Return exact means,variances,standardized squared discrepancies
and negative log likelihood scores0.5*(log(var)+discrepancy),omitting the
common0.5*log(2*pi) constant. Best label minimizes that floating score,
first supplied label wins exact score ties. ASCII lowercase labels1..8.
NOT_CLAIMED: simulator execution, multivariate composite likelihood,
statistical calibration, production readiness. Exact containers/caps.
"""
from fractions import Fraction
from math import log
ALPHABET='abcdefghijklmnopqrstuvwxyz'
SCOPE='PARTIAL: scalar Gaussian synthetic likelihood from supplied simulations only'
NOT_CLAIMED=('simulator execution','multivariate composite likelihood','statistical calibration','production readiness')


def _label(value):
    if type(value) is not str or not 1<=len(value)<=8 or any(c not in ALPHABET for c in value):
        raise ValueError('exact lowercase ASCII label required')


def _pair(value):
    return [value.numerator,value.denominator]


def compare(data):
    if type(data) is not dict or set(data)!={'observed','candidates'}:
        raise ValueError('exact dict with observed and candidates required')
    observed,candidates=data['observed'],data['candidates']
    if type(observed) is not int or not -9<=observed<=9:
        raise ValueError('observed must be an exact integer -9..9')
    if type(candidates) is not list or not 2<=len(candidates)<=6:
        raise ValueError('candidates must be an exact list of 2..6 records')
    seen=set()
    for record in candidates:
        if type(record) is not list or len(record)!=2:
            raise ValueError('candidate must be an exact pair list')
        label,samples=record
        _label(label)
        if label in seen:
            raise ValueError('candidate labels must be unique')
        seen.add(label)
        if type(samples) is not list or not 2<=len(samples)<=12:
            raise ValueError('samples must be an exact list of 2..12 values')
        for value in samples:
            if type(value) is not int or not -9<=value<=9:
                raise ValueError('samples must contain exact integers -9..9')
        if len(set(samples))==1:
            raise ValueError('sample variance must be positive')
    fitted={}
    best=None
    best_score=None
    for label,samples in candidates:
        mean=Fraction(sum(samples),len(samples))
        variance=sum((value-mean)**2 for value in samples)/(len(samples)-1)
        discrepancy=(observed-mean)**2/variance
        score=(log(float(variance))+float(discrepancy))/2
        fitted[label]={'mean':_pair(mean),'variance':_pair(variance),'discrepancy':_pair(discrepancy),'score':score}
        if best_score is None or score<best_score:
            best=label
            best_score=score
    return {'fitted':fitted,'best':best,'claims':[False,False,False,False]}

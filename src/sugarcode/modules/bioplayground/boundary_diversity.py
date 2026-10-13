"""Bounded probability-simplex wrapper for core.py:117-118 diversity metrics.

Legacy computes negative heterozygosity on invalid frequencies. No implicit
normalization: reject inputs outside the simplex before computation.
"""
import math
from .core import diversity_metrics as _legacy


def diversity_metrics(freq):
    if not isinstance(freq,(list,tuple)) or not 1<=len(freq)<=10000:
        raise ValueError('bounded nonempty probability list required')
    values=[]
    for v in freq:
        if isinstance(v,bool):raise ValueError('probability must not be bool')
        if not isinstance(v,(int,float)):raise ValueError('probability must be numeric')
        if abs(v)>1:raise ValueError('probability exceeds cap')
        if not math.isfinite(v) or v<0:raise ValueError('finite nonnegative probability required')
        values.append(float(v))
    if not math.isclose(math.fsum(values),1,rel_tol=0,abs_tol=1e-12):
        raise ValueError('probabilities must sum to one within 1e-12')
    # Zero entries are mathematically 0*log(0)=0, evaluated by omission.
    entropy=-math.fsum(x*math.log(x) for x in values if x)
    return {'heterozygosity':1-math.fsum(x*x for x in values),
            'shannon_entropy':entropy,'effective_alleles':math.exp(entropy),
            'model_status':'PARTIAL supplied-frequency diversity only; not organism robustness'}

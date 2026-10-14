"""Chemotherapy Planning.

PARTIAL: caller-supplied dose-budget arithmetic only, not chemotherapy planning,
prescribing, dose selection, eligibility or clinical safety assessment. No medical
limits inferred. Amounts and limits must be supplied by the caller in one unit.
"""
from fractions import Fraction
from math import isfinite
SCOPE='caller dose-budget arithmetic only; no prescribing or clinical safety'


def budget(amounts,limit):
    """Exactlist/tuple1..64 nonnegative finite built-in int/float amounts and limit,
    each <=1000000 in one caller unit. Decimal-spelling Fraction arithmetic.
    Return cumulative amounts, total, remaining (possibly negative), and inclusive
    over-limit flags. Input order is preserved; no dosing advice or unit inference.
    """
    def real(value):
        if type(value) not in (int,float) or not 0<=value<=1000000 or not isfinite(value):
            raise ValueError('amount must be finite built-in real0..1000000')
        return Fraction(str(value))
    cap=real(limit)
    if type(amounts) not in (list,tuple) or not 1<=len(amounts)<=64:
        raise ValueError('amounts must be exactlist/tuple length1..64')
    values=[real(value) for value in amounts];total=Fraction(0);cumulative=[]
    for value in values:
        total+=value;cumulative.append(total)
    return {'cumulative':tuple(cumulative),'total':total,'remaining':cap-total,
            'at_or_over':tuple(value>=cap for value in cumulative),'scope':SCOPE}

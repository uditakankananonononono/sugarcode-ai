"""Reforestation.

PARTIAL: caller cohort surviving-count ledger only, not reforestation,
ecological recovery,species suitability,carbon estimates or field validation.
Counts caller-declared,not proof of survival or restoration success.
"""
from fractions import Fraction
SCOPE='caller cohort count ledger only; no ecological recovery or carbon claims'


def cohorts(rows):
    """Exactlist/tuple1..64 rows(label,initial,surviving),unique printable Unicode
    exactstr1..40;exactint0<=surviving<=initial<=1000000. Return sorted(label,
    lost,exact surviving fraction or None if initial0),totals initial/surviving/
    lost and overall fraction(None if all initial0). No average of cohort ratios,
    time inference,causality or field verification. Mixedrows accepted.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];initial_total=0;surviving_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,initial,surviving=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(initial) is not int or type(surviving) is not int or not 0<=surviving<=initial<=1000000:raise ValueError('counts must be exactint0<=surviving<=initial<=1000000')
        result.append((label,initial-surviving,Fraction(surviving,initial) if initial else None));initial_total+=initial;surviving_total+=surviving
    return {'cohorts':tuple(sorted(result,key=lambda row:row[0])),'initial_total':initial_total,'surviving_total':surviving_total,
            'lost_total':initial_total-surviving_total,'fraction':Fraction(surviving_total,initial_total) if initial_total else None,'scope':SCOPE}

"""Exposure Science.

PARTIAL: caller concentration/duration product ledger only, not exposure
science, absorbed dose, route modeling, health assessment or safety advice.
Caller compatible quantities are abstract, not verified exposure measurements.
"""
from fractions import Fraction
SCOPE='caller concentration-duration product ledger only; no exposure or health claims'


def integrals(rows):
    """Exactlist/tuple1..64 triples(label,concentration,duration);printable
    Unicode exactstr labels1..40,repeated labels aggregate;exactint concentration
    0..1000000,duration1..1000000. Sorted(label,total duration,integral,
    weighted mean),total integral and duration. Mixedrows accepted;no route,
    absorption,bioavailability,time conversion or threshold inference.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,concentration,duration=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(concentration) is not int or type(duration) is not int or not 0<=concentration<=1000000 or not 1<=duration<=1000000:raise ValueError('concentration must be exactint0..1000000 and duration exactint1..1000000')
        old_duration,old_integral=groups.get(label,(0,0));groups[label]=(old_duration+duration,old_integral+concentration*duration)
    result=tuple((label,duration,integral,Fraction(integral,duration)) for label,(duration,integral) in sorted(groups.items()))
    return {'integrals':result,'total_integral':sum(row[2] for row in result),'total_duration':sum(row[1] for row in result),'scope':SCOPE}

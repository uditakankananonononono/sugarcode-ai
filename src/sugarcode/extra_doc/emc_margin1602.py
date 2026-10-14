"""Electromagnetic Compatibility.

PARTIAL: caller numeric measurement/limit margin arithmetic only, not EMC
assessment, testing, emissions prediction, certification or equipment safety.
Values/limits must be caller inputs in matching units and test conditions.
"""
from fractions import Fraction
from math import isfinite
SCOPE='caller numerical limit margins only; no EMC testing certification or safety'


def margins(rows):
    """Exactlist/tuple1..64 rows(label,measured,limit),unique printable Unicode
    exactstr label1..40; numbers finite exactbuilt-in int/float -1000000..
    1000000. Fraction decimal spelling. Margin=limit-measured, inclusive passes
    measured<=limit. Return sorted(label,margin,pass),minimum margin,all pass.
    No standards/units inferred, no dB conversion, no compliance certification.
    Mixedrowcontainers accepted both orders;caller must supply applicable limits.
    """
    def real(x):
        if type(x) not in (int,float) or not -1000000<=x<=1000000 or not isfinite(x):raise ValueError('number must be finite built-in real-1000000..1000000')
        return Fraction(str(x))
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,measured,limit=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label);measured=real(measured);limit=real(limit);result.append((label,limit-measured,measured<=limit))
    return {'margins':tuple(sorted(result,key=lambda row:row[0])),'minimum_margin':min(row[1] for row in result),
            'all_within':all(row[2] for row in result),'scope':SCOPE}

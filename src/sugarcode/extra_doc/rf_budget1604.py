"""RF Engineering.

PARTIAL: caller declared signed additive link-budget arithmetic only, not RF
engineering, measured propagation, range prediction, regulatory compliance or
hardware safety. Units and gains/losses are caller declarations, not inferred.
"""
from fractions import Fraction
from math import isfinite
SCOPE='caller signed additive link budget only; no RF propagation or compliance claims'


def budget(rows,initial,threshold):
    """Rows exactlist/tuple0..64 (label,signed contribution),unique printable
    Unicode exactstr1..40 labels;contribution/initial/threshold finite exact
    built-in int/float -1000000..1000000. Fraction decimal spelling. Preserve
    caller stage order;return(label,cumulative),final,margin=final-threshold,
    inclusive within final>=threshold. No path loss model,dB/unit conversions
    or claim of achievable performance. Mixedrowcontainers accepted.
    """
    def real(x):
        if type(x) not in (int,float) or not -1000000<=x<=1000000 or not isfinite(x):raise ValueError('number must be finite built-in real-1000000..1000000')
        return Fraction(str(x))
    total=real(initial);limit=real(threshold)
    if type(rows) not in (list,tuple) or len(rows)>64:raise ValueError('rows must be exactlist/tuple atmost64')
    labels=set();stages=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('row must be exactlist/tuple pair')
        label,contribution=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label);total+=real(contribution);stages.append((label,total))
    return {'stages':tuple(stages),'final':total,'margin':total-limit,'within':total>=limit,'scope':SCOPE}

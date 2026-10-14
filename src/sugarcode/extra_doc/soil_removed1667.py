"""Soil Remediation.

PARTIAL: caller initial/removed mass ledger only, not soil remediation,
contaminant testing, treatment selection, land safety or regulatory compliance.
Caller compatible masses are declarations, not verified cleanup outcomes.
"""
from fractions import Fraction
SCOPE='caller initial-removed mass ledger only; no soil remediation claims'


def remaining(rows):
    """Exactlist/tuple1..64 triples(label,initial,removed);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint0<=removed<=initial
    <=1000000. Sorted(label,initial total,removed total,residual,removed/initial
    or None at zero initial),total residual and aggregate removal fraction.
    Mixedrows accepted;no degradation,disposal,exposure or cleanup limits.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,initial,removed=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(initial) is not int or type(removed) is not int or not 0<=removed<=initial<=1000000:raise ValueError('masses must be exactint0<=removed<=initial<=1000000')
        old_initial,old_removed=groups.get(label,(0,0));groups[label]=(old_initial+initial,old_removed+removed)
    result=tuple((label,initial,removed,initial-removed,Fraction(removed,initial) if initial else None) for label,(initial,removed) in sorted(groups.items()))
    total_initial=sum(row[1] for row in result);total_removed=sum(row[2] for row in result)
    return {'remaining':result,'total_residual':total_initial-total_removed,'removal_fraction':Fraction(total_removed,total_initial) if total_initial else None,'scope':SCOPE}

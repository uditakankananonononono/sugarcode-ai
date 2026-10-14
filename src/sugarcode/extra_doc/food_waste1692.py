"""Food Waste.

PARTIAL: caller prepared/discarded quantity ledger only, not food waste
measurement, food safety, prevention effectiveness or environmental benefit.
Caller compatible quantities are declarations, not verified food waste data.
"""
from fractions import Fraction
SCOPE='caller prepared-discarded quantity ledger only; no verified food waste claims'


def waste(rows):
    """Exactlist/tuple1..64 triples(label,prepared,discarded);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint0<=discarded<=prepared
    <=1000000. Sorted(label,prepared total,discarded total,retained,discarded/prepared
    or None at zero prepared),total retained and aggregate removal fraction.
    Mixedrows accepted;no degradation,disposal,exposure or cleanup limits.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,prepared,discarded=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(prepared) is not int or type(discarded) is not int or not 0<=discarded<=prepared<=1000000:raise ValueError('masses must be exactint0<=discarded<=prepared<=1000000')
        old_prepared,old_discarded=groups.get(label,(0,0));groups[label]=(old_prepared+prepared,old_discarded+discarded)
    result=tuple((label,prepared,discarded,prepared-discarded,Fraction(discarded,prepared) if prepared else None) for label,(prepared,discarded) in sorted(groups.items()))
    total_prepared=sum(row[1] for row in result);total_discarded=sum(row[2] for row in result)
    return {'waste':result,'total_retained':total_prepared-total_discarded,'discarded_fraction':Fraction(total_discarded,total_prepared) if total_prepared else None,'scope':SCOPE}

"""Conservation Biology.

PARTIAL: caller category initial/final count arithmetic only, not conservation
biology, population viability, extinction risk or management recommendations.
Caller counts are declarations, not verified wildlife population measurements.
"""
from fractions import Fraction
SCOPE='caller initial-final count arithmetic only; no conservation biology claims'


def changes(rows):
    """Exactlist/tuple1..64 triples(label,initial,final);unique printable Unicode
    exactstr labels1..40;exactint counts0..1000000. Sorted(label,final-initial,
    final/initial or None at zero initial),strictly declining labels,total
    change. Mixedrows accepted;no births,deaths,migration,time or risk inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,initial,final=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(initial) is not int or type(final) is not int or not 0<=initial<=1000000 or not 0<=final<=1000000:raise ValueError('counts must be exactint0..1000000')
        parsed.append((label,final-initial,Fraction(final,initial) if initial else None))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'changes':result,'declining':tuple(row[0] for row in result if row[1]<0),'total_change':sum(row[1] for row in result),'scope':SCOPE}

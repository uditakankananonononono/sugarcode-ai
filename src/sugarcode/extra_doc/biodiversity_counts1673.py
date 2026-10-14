"""Biodiversity.

PARTIAL: caller category-count diversity arithmetic only, not biodiversity
surveying, species identification, ecosystem health or conservation assessment.
Caller categories and counts are not verified biological observations.
"""
from fractions import Fraction
SCOPE='caller category-count diversity arithmetic only; no biodiversity assessment claims'


def diversity(rows):
    """Exactlist/tuple1..64 pairs(label,count);printable Unicode exactstr
    labels1..40,repeats aggregate;exactint count0..1000000. Sorted counts,
    positive-count richness,total and 1-sum(squared category proportions),
    None at zero total. Zero categories retained but not rich. Mixedrows
    accepted;no species assumptions,sampling corrections or health inference.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('row must be exactlist/tuple pair')
        label,count=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(count) is not int or not 0<=count<=1000000:raise ValueError('count must be exactint0..1000000')
        groups[label]=groups.get(label,0)+count
    result=tuple(sorted(groups.items()));total=sum(groups.values())
    return {'counts':result,'total':total,'richness':sum(count>0 for label,count in result),'diversity':1-sum(Fraction(count,total)**2 for label,count in result) if total else None,'scope':SCOPE}

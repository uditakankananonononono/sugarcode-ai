"""Composting.

PARTIAL: caller carbon/nitrogen mixture arithmetic only, not composting,
feedstock testing, biological activity, safety or process recommendations.
Caller quantities have no inferred units or agronomic target ranges.
"""
from fractions import Fraction
SCOPE='caller carbon-nitrogen mixture arithmetic only; no composting advice'


def mixture(rows):
    """Exactlist/tuple1..64 triples(label,carbon,nitrogen);unique printable
    Unicode exactstr labels1..40;exactint quantities0..1000000. Sorted
    (label,carbon/nitrogen or None at zero nitrogen),total carbon,nitrogen
    and aggregate ratio (not mean of row ratios). Mixedrows accepted.
    No temperature,time,moisture,contamination or biological assumptions.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[];total_c=0;total_n=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,carbon,nitrogen=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(carbon) is not int or type(nitrogen) is not int or not 0<=carbon<=1000000 or not 0<=nitrogen<=1000000:raise ValueError('quantities must be exactint0..1000000')
        total_c+=carbon;total_n+=nitrogen;parsed.append((label,Fraction(carbon,nitrogen) if nitrogen else None))
    return {'components':tuple(sorted(parsed,key=lambda row:row[0])),'carbon':total_c,'nitrogen':total_n,'ratio':Fraction(total_c,total_n) if total_n else None,'scope':SCOPE}

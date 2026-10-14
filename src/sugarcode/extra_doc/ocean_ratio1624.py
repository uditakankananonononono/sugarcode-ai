"""Ocean Acidification.

PARTIAL: caller positive concentration-ratio arithmetic only, not ocean
acidification,carbonate chemistry,pH calculation or ecological projections.
Observations/reference are caller values without inferred units or chemistry.
"""
from fractions import Fraction
SCOPE='caller positive concentration ratios only; no ocean chemistry or pH predictions'


def ratios(rows,reference):
    """Rows exactlist/tuple1..64(label,num,den),unique printable Unicode exactstr
    label1..40;numerator/denominator exactint1..1000000. Reference exactlist/tuple
    pair of same positive component range. Return sorted(label,exact ratio of
    observation fraction to reference fraction,relative deviation ratio-1).
    No logarithms,pH conversion,speciation or climate assumptions. Mixedrows
    accepted;reference supplied by caller rather than a scientific baseline.
    """
    def fraction(row):
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('reference must be exactlist/tuple pair')
        num,den=row
        if type(num) is not int or type(den) is not int or not 1<=num<=1000000 or not 1<=den<=1000000:raise ValueError('fraction components must be exactint1..1000000')
        return Fraction(num,den)
    ref=fraction(reference)
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label);ratio=fraction((num,den))/ref;result.append((label,ratio,ratio-1))
    return {'ratios':tuple(sorted(result,key=lambda row:row[0])),'scope':SCOPE}

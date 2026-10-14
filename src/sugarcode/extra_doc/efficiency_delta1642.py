"""Energy Efficiency.

PARTIAL: caller before/after input arithmetic only, not energy efficiency,
normalized performance,verified savings or financial/environmental impacts.
Values caller declarations,no equal-service or comparable conditions validated.
"""
from fractions import Fraction
SCOPE='caller before-after input arithmetic only; no verified energy savings or efficiency claims'


def changes(rows):
    """Exactlist/tuple1..64 rows(label,before,after),unique printable Unicode
    exactstr1..40;before/after exactint0..1000000. Return sorted(label,before-after,
    fractional change=(before-after)/before or None if before0),totals before/
    after/difference,aggregate fraction(None if total before0). Negative savings
    allowed. No service-output,weather,occupancy,tariff or cost inference.
    Mixedrows accepted;arithmetic difference not verified efficiency improvement.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];before_total=0;after_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,before,after=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(before) is not int or type(after) is not int or not 0<=before<=1000000 or not 0<=after<=1000000:raise ValueError('inputs must be exactint0..1000000')
        delta=before-after;result.append((label,delta,Fraction(delta,before) if before else None));before_total+=before;after_total+=after
    delta=before_total-after_total
    return {'changes':tuple(sorted(result,key=lambda row:row[0])),'before_total':before_total,'after_total':after_total,
            'difference':delta,'aggregate_fraction':Fraction(delta,before_total) if before_total else None,'scope':SCOPE}

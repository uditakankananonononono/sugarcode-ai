"""Renewable Energy.

PARTIAL: caller generation-unit portfolio arithmetic only, not renewable energy
production,grid integration,emissions savings or validated resource forecasts.
Amounts/source flags caller declarations,not measured or certified generation.
"""
from fractions import Fraction
SCOPE='caller generation-unit portfolio arithmetic only; no renewable output or emissions claims'


def mix(rows):
    """Exactlist/tuple1..64 rows(label,amount,renewable),unique printable Unicode
    exactstr1..40;amount exactint0..1000000,renewable exactbool. Return sorted
    (label,amount,flag),totals amount/flagged/unflagged and flagged fraction(None
    if total0). Flags not certified source classifications. Mixedrows accepted.
    No units,capacity factors,storage,grid behavior or environmental impacts.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,amount,renewable=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(amount) is not int or not 0<=amount<=1000000:raise ValueError('amount must be exactint0..1000000')
        if type(renewable) is not bool:raise ValueError('renewable flag must be exactbool')
        result.append((label,amount,renewable))
    total=sum(row[1] for row in result);flagged=sum(row[1] for row in result if row[2])
    return {'portfolio':tuple(sorted(result,key=lambda row:row[0])),'total':total,'flagged_total':flagged,
            'unflagged_total':total-flagged,'flagged_fraction':Fraction(flagged,total) if total else None,'scope':SCOPE}

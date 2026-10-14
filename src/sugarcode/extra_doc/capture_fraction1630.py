"""Carbon Capture.

PARTIAL: caller stream fraction ledger arithmetic only, not carbon capture,
separation physics,efficiency certification,emissions accounting or cost analysis.
Input quantities/fractions caller-declared,not measured or validated process data.
"""
from fractions import Fraction
SCOPE='caller stream fraction ledger only; no capture efficiency or emissions claims'


def streams(rows):
    """Exactlist/tuple1..64 rows(label,amount,num,den),unique printable Unicode
    exactstr label1..40;amount exactint0..1000000,fraction exactints0<=num<=den
    <=1000000 with den>0. Return sorted(label,retained,remainder),totals retained/
    remainder/input,and retained/input exact fraction or None if input0. No
    lifecycle emissions,capture technology,energy,storage or physical inference.
    Mixedrows accepted;retained only caller fraction,not demonstrated capture.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];input_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple four values')
        label,amount,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(amount) is not int or not 0<=amount<=1000000:raise ValueError('amount must be exactint0..1000000')
        if type(num) is not int or type(den) is not int or not 0<=num<=den<=1000000 or den==0:raise ValueError('fraction components must be exactint0<=num<=den<=1000000 and den>0')
        retained=amount*Fraction(num,den);result.append((label,retained,amount-retained));input_total+=amount
    retained=sum((row[1] for row in result),Fraction(0));remainder=sum((row[2] for row in result),Fraction(0))
    return {'streams':tuple(sorted(result,key=lambda row:row[0])),'input_total':input_total,'retained_total':retained,
            'remainder_total':remainder,'retained_fraction':retained/input_total if input_total else None,'scope':SCOPE}

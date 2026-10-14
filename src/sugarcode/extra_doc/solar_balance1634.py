"""Solar Radiation Management.

PARTIAL: caller incoming/reflected arithmetic only, not solar radiation
management,radiative forcing,climate response,interventions or safety.
Inputs are caller abstractions,no physical calibration or planetary assumptions.
"""
from fractions import Fraction
SCOPE='caller incoming/reflected arithmetic only; no radiative forcing or intervention claims'


def balance(rows):
    """Exactlist/tuple1..64 rows(label,incoming,reflect_num,reflect_den),unique
    printable Unicode exactstr1..40 labels;incoming exactint0..1000000,fraction
    components exactints0<=num<=den<=1000000,den>0. Return sorted(label,reflected,
    remainder),totals incoming/reflected/remainder. Fractions exact. No geometry,
    absorption physics,temperature response,wavelength dependence or advice.
    Mixedrows accepted;remainder only arithmetic difference,not proven absorption.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];incoming_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple four values')
        label,incoming,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(incoming) is not int or not 0<=incoming<=1000000:raise ValueError('incoming must be exactint0..1000000')
        if type(num) is not int or type(den) is not int or not 0<=num<=den<=1000000 or den==0:raise ValueError('fraction components must be exactint0<=num<=den<=1000000 and den>0')
        reflected=Fraction(incoming*num,den);result.append((label,reflected,incoming-reflected));incoming_total+=incoming
    return {'balance':tuple(sorted(result,key=lambda row:row[0])),'incoming_total':incoming_total,
            'reflected_total':sum((row[1] for row in result),Fraction(0)),
            'remainder_total':sum((row[2] for row in result),Fraction(0)),'scope':SCOPE}

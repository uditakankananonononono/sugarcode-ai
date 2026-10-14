"""Soil Carbon.

PARTIAL: caller weighted layer-value arithmetic only, not soil carbon,
stock measurement,bulk-density inference,sequestration or field validation.
Weights/values caller abstractions,not measured soil depths or concentrations.
"""
from fractions import Fraction
SCOPE='caller weighted layer-value arithmetic only; no soil carbon stock or sequestration claims'


def layers(rows):
    """Exactlist/tuple1..64 rows(label,weight,value),unique printable Unicode
    exactstr1..40;weight exactint1..1000000,value exactint0..1000000. Return
    sorted(label,weight*value),total weight,total weighted value and exact mean.
    No units,depth,density,area or physical conversion inferred. Mixedrows
    accepted;weights caller-defined,not necessarily comparable physical masses.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];weight_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,weight,value=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(weight) is not int or not 1<=weight<=1000000:raise ValueError('weight must be exactint1..1000000')
        if type(value) is not int or not 0<=value<=1000000:raise ValueError('value must be exactint0..1000000')
        result.append((label,weight*value));weight_total+=weight
    total=sum(value for _,value in result)
    return {'weighted':tuple(sorted(result,key=lambda row:row[0])),'weight_total':weight_total,'weighted_total':total,'mean':Fraction(total,weight_total),'scope':SCOPE}

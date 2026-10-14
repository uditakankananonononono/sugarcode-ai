"""Sustainable Transport.

PARTIAL: caller trip passenger/distance totals only, not sustainable transport,
emissions modeling,mode recommendations,routing or environmental evaluation.
Distances/passengers caller declarations,no real trips or vehicle data inferred.
"""
from fractions import Fraction
SCOPE='caller trip passenger-distance totals only; no sustainability or routing claims'


def trips(rows):
    """Exactlist/tuple1..64 rows(label,distance,passengers),unique printable Unicode
    exactstr1..40;distance exactint0..1000000,passengers exactint0..1000. Return
    sorted(label,distance*passengers),distance total,passenger-distance total,
    distance-weighted passengers(None if distance0). No capacity,fuel,emissions,
    routes,time or mode suitability inferred. Mixedrows accepted.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];distance_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,distance,passengers=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(distance) is not int or not 0<=distance<=1000000:raise ValueError('distance must be exactint0..1000000')
        if type(passengers) is not int or not 0<=passengers<=1000:raise ValueError('passengers must be exactint0..1000')
        result.append((label,distance*passengers));distance_total+=distance
    total=sum(value for _,value in result)
    return {'passenger_distances':tuple(sorted(result,key=lambda row:row[0])),'distance_total':distance_total,
            'passenger_distance_total':total,'weighted_passengers':Fraction(total,distance_total) if distance_total else None,'scope':SCOPE}

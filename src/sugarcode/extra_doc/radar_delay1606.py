"""Radar Systems.

PARTIAL: caller round-trip delay distance arithmetic only, not radar systems,
object detection, tracking, propagation modeling or measurement validation.
Caller speed and delay units must match; no physical constants or targets inferred.
"""
from fractions import Fraction
SCOPE='caller round-trip delay distance arithmetic only; no radar detection or tracking'


def ranges(rows,speed):
    """Rows exactlist/tuple1..64 (label,delay_num,delay_den),unique printable
    Unicode exactstr1..40 labels. Delay numerator exactint0..1000000,denominator
    exactint1..1000000;speed exactint1..1000000000. Return label-sorted exact
    distance=speed*delay_num/(2*delay_den),and min/max distance. No uncertainty,
    multipath,Doppler,ambiguity or object identification. Mixedrows accepted.
    """
    if type(speed) is not int or not 1<=speed<=1000000000:raise ValueError('speed must be exactint1..1000000000')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(num) is not int or not 0<=num<=1000000:raise ValueError('delay numerator must be exactint0..1000000')
        if type(den) is not int or not 1<=den<=1000000:raise ValueError('delay denominator must be exactint1..1000000')
        result.append((label,Fraction(speed*num,2*den)))
    return {'ranges':tuple(sorted(result,key=lambda row:row[0])),'minimum':min(row[1] for row in result),
            'maximum':max(row[1] for row in result),'scope':SCOPE}

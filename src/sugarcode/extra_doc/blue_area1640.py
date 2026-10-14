"""Blue Carbon.

PARTIAL: caller area/intensity product arithmetic only, not blue carbon,
ecosystem stocks,sequestration rates,restoration benefits or credit validation.
Area/intensity caller declarations,not scientifically verified coastal data.
"""
from fractions import Fraction
SCOPE='caller area-intensity products only; no coastal carbon stocks or credit claims'


def products(rows):
    """Exactlist/tuple1..64 rows(label,area,intensity_num,intensity_den),unique
    printable Unicode exactstr1..40;area/numerator exactint0..1000000,
    denominator exactint1..1000000. Return sorted(label,exact area*num/den),total
    area,total product,and area-weighted intensity(None if area0). No time,
    species,boundaries,carbon units,additionality or ecological inference.
    Mixedrows accepted;products only caller arithmetic,not measured stocks.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];area_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple four values')
        label,area,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(area) is not int or type(num) is not int or not 0<=area<=1000000 or not 0<=num<=1000000:raise ValueError('area and numerator must be exactint0..1000000')
        if type(den) is not int or not 1<=den<=1000000:raise ValueError('denominator must be exactint1..1000000')
        result.append((label,Fraction(area*num,den)));area_total+=area
    total=sum((value for _,value in result),Fraction(0))
    return {'products':tuple(sorted(result,key=lambda row:row[0])),'area_total':area_total,'product_total':total,
            'weighted_intensity':total/area_total if area_total else None,'scope':SCOPE}

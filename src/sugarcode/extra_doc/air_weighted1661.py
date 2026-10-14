"""Air Quality.

PARTIAL: caller observation/duration weighted mean only, not air quality
measurement, pollutant identification, exposure assessment or health advice.
Caller values have no inferred units, safety bands or regulatory thresholds.
"""
from fractions import Fraction
SCOPE='caller observation-duration weighted means only; no air quality or health claims'


def means(rows):
    """Exactlist/tuple1..64 triples(label,value,duration);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint value0..1000000,
    duration1..1000000. Sorted(label,total duration,weighted mean),overall
    duration and weighted mean. Mixedrows accepted. Independent caller
    observations only,no sampling validation,time alignment or unit conversion.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,value,duration=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(value) is not int or type(duration) is not int or not 0<=value<=1000000 or not 1<=duration<=1000000:raise ValueError('value must be exactint0..1000000 and duration exactint1..1000000')
        old_duration,old_weighted=groups.get(label,(0,0));groups[label]=(old_duration+duration,old_weighted+value*duration)
    result=tuple((label,duration,Fraction(weighted,duration)) for label,(duration,weighted) in sorted(groups.items()))
    total_duration=sum(duration for duration,weighted in groups.values());total_weighted=sum(weighted for duration,weighted in groups.values())
    return {'means':result,'duration':total_duration,'overall_mean':Fraction(total_weighted,total_duration),'scope':SCOPE}

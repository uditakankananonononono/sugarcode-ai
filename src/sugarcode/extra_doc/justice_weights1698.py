"""Environmental Justice.

PARTIAL: caller group value/population weighted arithmetic only, not
 environmental justice, fairness, discrimination or policy assessment.
Caller groups and values are abstract, not verified demographics or burdens.
"""
from fractions import Fraction
SCOPE='caller group-value-population weighted arithmetic only; no environmental justice assessment'


def weights(rows):
    """Exactlist/tuple1..64 triples(label,value,population);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint value0..1000000,
    population1..1000000. Sorted(label,total population,weighted mean),overall
    weighted mean,range of group means. Mixedrows accepted;differences are
    arithmetic only,no injustice,causality,protected status or policy inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,value,population=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(value) is not int or type(population) is not int or not 0<=value<=1000000 or not 1<=population<=1000000:raise ValueError('value must be exactint0..1000000 and population exactint1..1000000')
        old_population,old_weighted=groups.get(label,(0,0));groups[label]=(old_population+population,old_weighted+value*population)
    result=tuple((label,population,Fraction(weighted,population)) for label,(population,weighted) in sorted(groups.items()))
    total_population=sum(p for p,w in groups.values());total_weighted=sum(w for p,w in groups.values());means=[row[2] for row in result]
    return {'weights':result,'overall_mean':Fraction(total_weighted,total_population),'range':max(means)-min(means),'scope':SCOPE}

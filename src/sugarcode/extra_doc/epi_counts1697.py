"""Epidemiology.

PARTIAL: caller case/population count fractions only, not epidemiology,
incidence prediction, causal inference, diagnosis or public-health advice.
Caller counts are abstract, not verified cases, cohorts or surveillance data.
"""
from fractions import Fraction
SCOPE='caller case-population count fractions only; no epidemiological or health claims'


def fractions(rows):
    """Exactlist/tuple1..64 triples(label,cases,population);unique printable
    Unicode exactstr labels1..40;exactint0<=cases<=population<=1000000 with
    population>0. Sorted(label,cases/population),total cases,population and
    aggregate fraction. Mixedrows accepted;no time,selection,bias correction,
    diagnoses,transmission or cohort overlap assumptions inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[];total_cases=0;total_population=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,cases,population=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(cases) is not int or type(population) is not int or not 0<=cases<=population<=1000000 or population==0:raise ValueError('counts must be exactint0<=cases<=population<=1000000 with population>0')
        total_cases+=cases;total_population+=population;parsed.append((label,Fraction(cases,population)))
    return {'fractions':tuple(sorted(parsed,key=lambda row:row[0])),'cases':total_cases,'population':total_population,'aggregate_fraction':Fraction(total_cases,total_population),'scope':SCOPE}

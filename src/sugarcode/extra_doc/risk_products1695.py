"""Risk Assessment.

PARTIAL: caller probability/severity arithmetic only, not risk assessment,
validated likelihood, health/safety classification or management advice.
Caller severities and probability fractions are abstract, not calibrated risks.
"""
from fractions import Fraction
SCOPE='caller probability-severity arithmetic only; no validated risk assessment claims'


def scores(rows,threshold):
    """Exactlist/tuple1..64 quads(label,numerator,denominator,severity);unique
    printable Unicode exactstr labels1..40;exactint0<=numerator<=denominator
    <=1000000,denominator>0,severity0..1000000;threshold exactint0..1000000.
    Sorted(label,probability*severity),strictly above caller threshold labels,
    total score. Mixedrows accepted;no independence or real risk meaning inferred.
    """
    if type(threshold) is not int or not 0<=threshold<=1000000:raise ValueError('threshold must be exactint0..1000000')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,numerator,denominator,severity=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(numerator) is not int or type(denominator) is not int or type(severity) is not int or not 0<=numerator<=denominator<=1000000 or denominator==0 or not 0<=severity<=1000000:raise ValueError('probability must be exactint0<=numerator<=denominator<=1000000 with denominator>0 and severity exactint0..1000000')
        parsed.append((label,Fraction(numerator,denominator)*severity))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'scores':result,'above':tuple(label for label,value in result if value>threshold),'total_score':sum(value for label,value in result),'scope':SCOPE}

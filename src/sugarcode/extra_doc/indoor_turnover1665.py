"""Indoor Air Quality.

PARTIAL: caller airflow/volume ratio arithmetic only, not indoor air quality,
ventilation adequacy, exposure assessment or health/safety recommendations.
Caller compatible quantities are not verified room or ventilation measurements.
"""
from fractions import Fraction
SCOPE='caller airflow-volume ratios only; no indoor air quality or safety claims'


def turnover(rows,threshold):
    """Exactlist/tuple1..64 triples(label,airflow,volume);unique printable
    Unicode exactstr labels1..40;exactint airflow0..1000000,volume1..1000000;
    threshold exactint0..1000000 caller comparison only. Sorted(label,ratio),
    strictly below labels,minimum ratio. Mixedrows accepted. No time conversion,
    contaminant transport,filtration or recommended ventilation limits inferred.
    """
    if type(threshold) is not int or not 0<=threshold<=1000000:raise ValueError('threshold must be exactint0..1000000')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,airflow,volume=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(airflow) is not int or type(volume) is not int or not 0<=airflow<=1000000 or not 1<=volume<=1000000:raise ValueError('airflow must be exactint0..1000000 and volume exactint1..1000000')
        parsed.append((label,Fraction(airflow,volume)))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'turnover':result,'below':tuple(label for label,ratio in result if ratio<threshold),'minimum':min(ratio for label,ratio in result),'scope':SCOPE}

"""Water Quality.

PARTIAL: caller measurement/bound comparison only, not water quality testing,
potability, contaminant identification, health advice or regulatory compliance.
Caller bounds are arbitrary comparisons, not drinking-water standards.
"""
SCOPE='caller measurement-bound comparisons only; no water quality or safety claims'


def compare(rows):
    """Exactlist/tuple1..64 quads(label,value,lower,upper);unique printable
    Unicode exactstr labels1..40;exactint value0..1000000,0<=lower<=upper
    <=1000000. Sorted(label,below/within/above,value-lower,upper-value),strictly
    outside labels and count within inclusive bounds. Mixedrows accepted.
    No units,acceptable exposure or environmental conclusions inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,value,lower,upper=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(value) is not int or type(lower) is not int or type(upper) is not int or not 0<=value<=1000000 or not 0<=lower<=upper<=1000000:raise ValueError('values must be exactint0..1000000 with lower<=upper')
        status='below' if value<lower else ('above' if value>upper else 'within')
        parsed.append((label,status,value-lower,upper-value))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'comparisons':result,'outside':tuple(row[0] for row in result if row[1]!='within'),'within_count':sum(row[1]=='within' for row in result),'scope':SCOPE}

"""Environmental Impact Assessment.

PARTIAL: caller magnitude/extent/duration score arithmetic only, not an
 environmental impact assessment, significance finding or regulatory review.
Caller scores are abstract, not validated environmental effects or evidence.
"""
SCOPE='caller magnitude-extent-duration products only; no environmental impact assessment'


def impacts(rows):
    """Exactlist/tuple1..64 quads(label,magnitude,extent,duration);unique
    printable Unicode exactstr labels1..40;exactint scores0..1000000.
    Sorted(label,product),total and zero-product labels. Mixedrows accepted.
    No units,causality,significance,mitigation or legal conclusions inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,magnitude,extent,duration=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(magnitude) is not int or type(extent) is not int or type(duration) is not int or not 0<=magnitude<=1000000 or not 0<=extent<=1000000 or not 0<=duration<=1000000:raise ValueError('scores must be exactint0..1000000')
        parsed.append((label,magnitude*extent*duration))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'impacts':result,'total':sum(value for label,value in result),'zero':tuple(label for label,value in result if value==0),'scope':SCOPE}

"""Stakeholder Analysis.

PARTIAL: caller influence/interest threshold grid only, not stakeholder
analysis, relationship assessment, consent, outreach or engagement advice.
Caller scores and thresholds are abstract, not verified stakeholder attributes.
"""
SCOPE='caller influence-interest threshold grid only; no stakeholder assessment or outreach'


def grid(rows,threshold):
    """Exactlist/tuple1..64 triples(label,influence,interest);unique printable
    Unicode exactstr labels1..40;exactint scores and threshold0..1000000.
    Sorted(label,influence>=threshold,interest>=threshold),both-high labels
    and count of each Boolean pair in False/False,False/True,True/False,True/True
    order. Mixedrows accepted;no people,priorities,permissions or plans inferred.
    """
    if type(threshold) is not int or not 0<=threshold<=1000000:raise ValueError('threshold must be exactint0..1000000')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,influence,interest=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(influence) is not int or type(interest) is not int or not 0<=influence<=1000000 or not 0<=interest<=1000000:raise ValueError('scores must be exactint0..1000000')
        parsed.append((label,influence>=threshold,interest>=threshold))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    counts=tuple((x,y,sum(row[1]==x and row[2]==y for row in result)) for x,y in ((False,False),(False,True),(True,False),(True,True)))
    return {'grid':result,'counts':counts,'both_high':tuple(label for label,x,y in result if x and y),'scope':SCOPE}

"""Circular Economy.

PARTIAL: caller incoming/outgoing resource ledger only, not circular economy,
material-flow certification,lifecycle analysis or sustainability assessment.
Flows are caller-declared,not verified sourcing,reuse,recycling or disposal data.
"""
SCOPE='caller incoming-outgoing resource ledger only; no circularity or sustainability claims'


def flows(rows):
    """Exactlist/tuple1..64 rows(label,incoming,outgoing),printable Unicode exactstr
    label1..40,repeats aggregate;exactint quantities0..1000000. Return sorted
    (label,incoming sum,outgoing sum,balance incoming-outgoing),positive/negative
    label balances and total net. No stock carryover,physical units or implied
    circularity,closed loop,origin/destination verified. Mixedrows accepted.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,incoming,outgoing=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(incoming) is not int or type(outgoing) is not int or not 0<=incoming<=1000000 or not 0<=outgoing<=1000000:raise ValueError('flows must be exactint0..1000000')
        before_in,before_out=groups.get(label,(0,0));groups[label]=(before_in+incoming,before_out+outgoing)
    result=tuple((label,incoming,outgoing,incoming-outgoing) for label,(incoming,outgoing) in sorted(groups.items()))
    return {'flows':result,'positive':tuple(row[0] for row in result if row[3]>0),
            'negative':tuple(row[0] for row in result if row[3]<0),'net_total':sum(row[3] for row in result),'scope':SCOPE}

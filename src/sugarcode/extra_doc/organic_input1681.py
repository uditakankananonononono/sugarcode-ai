"""Organic Farming.

PARTIAL: caller area/input-rate product ledger only, not organic farming,
organic certification, input eligibility, crop yield or agronomic advice.
Caller compatible quantities are declarations, not verified farming data.
"""
SCOPE='caller area-input-rate product ledger only; no organic farming or certification claims'


def inputs(rows):
    """Exactlist/tuple1..64 triples(label,area,rate);printable Unicode exactstr
    labels1..40,repeats aggregate;exactint quantities0..1000000. Sorted(label,
    area sum,sum area*rate),total input and strictly positive-input labels.
    Mixedrows accepted;no units,approved inputs,application limits or outcomes.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,area,rate=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(area) is not int or type(rate) is not int or not 0<=area<=1000000 or not 0<=rate<=1000000:raise ValueError('quantities must be exactint0..1000000')
        old_area,old_input=groups.get(label,(0,0));groups[label]=(old_area+area,old_input+area*rate)
    result=tuple((label,area,quantity) for label,(area,quantity) in sorted(groups.items()))
    return {'inputs':result,'total_input':sum(row[2] for row in result),'positive':tuple(row[0] for row in result if row[2]>0),'scope':SCOPE}

"""Negative Emissions.

PARTIAL: caller removal/emission bookkeeping only, not negative-emissions
validation,carbon credits,lifecycle analysis or net-zero certification.
Amounts supplied by caller,not verified removals or emissions inventories.
"""
SCOPE='caller removal-emission bookkeeping only; no carbon credits or net-zero certification'


def net(rows):
    """Rows exactlist/tuple1..64(label,removed,emitted),unique printable Unicode
    exactstr label1..40;removed/emitted exactint0..1000000. Return sorted(label,
    removed-emitted),totals removed/emitted/net,and positive-net labels. Positive
    ledger net only denotes supplied removed>emitted,not demonstrated climate
    benefit,additionality,durability or a tradeable credit. Mixedrows accepted.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];removed_total=0;emitted_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,removed,emitted=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(removed) is not int or type(emitted) is not int or not 0<=removed<=1000000 or not 0<=emitted<=1000000:raise ValueError('amounts must be exactint0..1000000')
        result.append((label,removed-emitted));removed_total+=removed;emitted_total+=emitted
    result.sort(key=lambda row:row[0])
    return {'net':tuple(result),'removed_total':removed_total,'emitted_total':emitted_total,'net_total':removed_total-emitted_total,
            'positive':tuple(label for label,value in result if value>0),'scope':SCOPE}

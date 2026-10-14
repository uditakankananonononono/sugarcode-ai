"""Emissions Monitoring.

PARTIAL: caller ordered emission-value differences only, not emissions
monitoring, sensor validation, source attribution or regulatory compliance.
Caller values are abstract, not verified pollutant measurements.
"""
SCOPE='caller ordered value-difference arithmetic only; no emissions monitoring claims'


def changes(rows):
    """Exactlist/tuple1..64 pairs(label,value);unique printable Unicode
    exactstr labels1..40;exactint value0..1000000. Preserve order;return
    (label,value,difference from previous or None for first),strict increases,
    total telescoping change and maximum value. Mixedrows accepted.
    No timestamps,time normalization,units,limits or alerts inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('row must be exactlist/tuple pair')
        label,value=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(value) is not int or not 0<=value<=1000000:raise ValueError('value must be exactint0..1000000')
        parsed.append((label,value))
    result=tuple((label,value,value-parsed[index-1][1] if index else None) for index,(label,value) in enumerate(parsed))
    return {'changes':result,'increases':tuple(label for label,value,delta in result if delta is not None and delta>0),'total_change':parsed[-1][1]-parsed[0][1],'maximum':max(value for label,value in parsed),'scope':SCOPE}

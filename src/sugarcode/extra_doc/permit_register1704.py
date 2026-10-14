"""Permitting.

PARTIAL: caller-declared permit-stage register only, not permitting,
application submission, legal eligibility, approval verification or legal advice.
Caller stage labels are not verified permits or authority to proceed.
"""
SCOPE='caller-declared permit-stage register only; no permitting or approval claims'


def records(rows):
    """Exactlist/tuple1..64 triples(label,status,count);unique printable Unicode
    exactstr labels1..40;status exactstr draft/submitted/returned;count exactint
    0..1000000. Sorted rows,status counts and totals,strictly returned labels.
    Mixedrows accepted;status values are caller categories with no legal,
    ethical or community meaning inferred. No real-world actions authorized.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,status,count=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(status) is not str or status not in ('draft','submitted','returned'):raise ValueError('status must be exactstr draft/submitted/returned')
        if type(count) is not int or not 0<=count<=1000000:raise ValueError('count must be exactint0..1000000')
        parsed.append((label,status,count))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    summaries=tuple((status,sum(row[1]==status for row in result),sum(row[2] for row in result if row[1]==status)) for status in ('draft','submitted','returned'))
    return {'records':result,'statuses':summaries,'returned':tuple(row[0] for row in result if row[1]=='returned'),'scope':SCOPE}

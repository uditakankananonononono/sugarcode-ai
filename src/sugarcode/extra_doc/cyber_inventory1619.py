"""Cybersecurity.

PARTIAL: caller patch-version inventory comparison only, not cybersecurity,
vulnerability discovery, secure-version certification or remediation execution.
Required versions supplied by caller; version ordering is integer-only toy data.
"""
SCOPE='caller integer version inventory comparison only; no vulnerability or security claims'


def inventory(rows):
    """Exactlist/tuple1..64 rows(label,current,required),unique printable Unicode
    exactstr label1..40;versions exactint0..1000000. Return label-sorted
    (label,required-current,is_below),below labels, and largest positive gap.
    Version numbers are caller ordinal integers,not semantic version strings.
    Equality and later versions not below. Mixedrows accepted. No patches
    downloaded,installed or recommended; no claim any version is secure.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,current,required=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(current) is not int or type(required) is not int or not 0<=current<=1000000 or not 0<=required<=1000000:raise ValueError('versions must be exactint0..1000000')
        result.append((label,required-current,current<required))
    result.sort(key=lambda row:row[0])
    return {'inventory':tuple(result),'below':tuple(label for label,gap,below in result if below),
            'largest_gap':max(max(row[1],0) for row in result),'scope':SCOPE}

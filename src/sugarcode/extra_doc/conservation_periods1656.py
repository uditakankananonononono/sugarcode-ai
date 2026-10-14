"""Water Conservation.

PARTIAL: caller baseline/current/period savings arithmetic only, not water
conservation, verified consumption, environmental benefit or policy advice.
Quantities and periods are caller abstractions, not measured water-use data.
"""
SCOPE='caller baseline-current-period arithmetic only; no verified water conservation claims'


def savings(rows):
    """Exactlist/tuple1..64 quads(label,baseline,current,periods);printable
    Unicode exactstr labels1..40,repeats aggregate;exactint quantities0..1000000,
    periods1..1000000. Sorted(label,total baseline,total current,savings),
    total savings and strictly negative savings labels. Negative values not
    clamped. Mixedrows accepted;no units,tariffs or extrapolation inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,baseline,current,periods=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(baseline) is not int or type(current) is not int or type(periods) is not int or not 0<=baseline<=1000000 or not 0<=current<=1000000 or not 1<=periods<=1000000:raise ValueError('quantities must be exactint0..1000000 and periods exactint1..1000000')
        old_base,old_current=groups.get(label,(0,0));groups[label]=(old_base+baseline*periods,old_current+current*periods)
    result=tuple((label,baseline,current,baseline-current) for label,(baseline,current) in sorted(groups.items()))
    return {'savings':result,'total_savings':sum(row[3] for row in result),'negative':tuple(row[0] for row in result if row[3]<0),'scope':SCOPE}

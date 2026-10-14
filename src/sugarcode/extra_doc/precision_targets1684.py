"""Precision Agriculture.

PARTIAL: caller area/current/target input arithmetic only, not precision
agriculture, sensor calibration, crop optimization or application advice.
Caller rates are declarations, not agronomic targets or verified measurements.
"""
SCOPE='caller area-current-target input arithmetic only; no precision agriculture advice'


def adjustments(rows):
    """Exactlist/tuple1..64 quads(label,area,current rate,target rate);unique
    printable Unicode exactstr labels1..40;exactint quantities0..1000000.
    Sorted(label,current total,target total,signed adjustment),total adjustment
    and strictly positive adjustment labels. Mixedrows accepted;no variable
    rate equipment,safety,units,nutrient need or yield recommendation inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,area,current,target=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(area) is not int or type(current) is not int or type(target) is not int or not 0<=area<=1000000 or not 0<=current<=1000000 or not 0<=target<=1000000:raise ValueError('quantities must be exactint0..1000000')
        current_total=area*current;target_total=area*target;parsed.append((label,current_total,target_total,target_total-current_total))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'adjustments':result,'total_adjustment':sum(row[3] for row in result),'positive':tuple(row[0] for row in result if row[3]>0),'scope':SCOPE}

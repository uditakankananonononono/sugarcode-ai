"""Vertical Farming.

PARTIAL: caller footprint/layers/output-rate arithmetic only, not vertical
farming, crop growth, lighting design, yield prediction or economic advice.
Caller factors are abstract, not verified equipment or crop performance data.
"""
SCOPE='caller footprint-layers-output-rate arithmetic only; no vertical farming claims'


def layers(rows):
    """Exactlist/tuple1..64 quads(label,footprint,layers,rate);unique printable
    Unicode exactstr labels1..40;exactint footprint,rate0..1000000,layers1..64.
    Sorted(label,total growing area,area*rate),total area and total product.
    Mixedrows accepted;no actual yields,spacing,energy,units or costs inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,footprint,count,rate=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(footprint) is not int or type(count) is not int or type(rate) is not int or not 0<=footprint<=1000000 or not 1<=count<=64 or not 0<=rate<=1000000:raise ValueError('footprint and rate must be exactint0..1000000 and layers exactint1..64')
        area=footprint*count;parsed.append((label,area,area*rate))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'layers':result,'total_area':sum(row[1] for row in result),'total_product':sum(row[2] for row in result),'scope':SCOPE}

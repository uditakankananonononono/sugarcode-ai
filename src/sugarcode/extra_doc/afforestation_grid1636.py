"""Afforestation.

PARTIAL: caller rectangular interior lattice count arithmetic only, not
afforestation,ecological suitability,planting recommendations or carbon estimates.
Plot dimensions/spacing are caller abstractions,no terrain or species inferred.
"""
SCOPE='caller rectangular interior lattice counts only; no planting or carbon recommendations'


def plots(rows,spacing):
    """Exactlist/tuple1..64 rows(label,length,width),unique printable Unicode
    exactstr1..40;dimensions exactint0..1000000,spacing exactint1..1000000.
    Sites at positive spacing multiples strictly inside each dimension;counts
    max((dimension-1)//spacing,0). Return sorted(label,lengthcount,widthcount,
    product),total sites. Boundary sites excluded;zero dimensions supported.
    Mixedrows accepted. No planting density standards,physical layout or advice.
    """
    if type(spacing) is not int or not 1<=spacing<=1000000:raise ValueError('spacing must be exactint1..1000000')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,length,width=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(length) is not int or type(width) is not int or not 0<=length<=1000000 or not 0<=width<=1000000:raise ValueError('dimensions must be exactint0..1000000')
        n=max((length-1)//spacing,0);m=max((width-1)//spacing,0);result.append((label,n,m,n*m))
    return {'plots':tuple(sorted(result,key=lambda row:row[0])),'total_sites':sum(row[3] for row in result),'scope':SCOPE}

"""Aquaponics.

PARTIAL: caller input/uptake/loss nutrient ledger only, not aquaponics,
fish or plant health, nutrient cycling, water safety or operational advice.
Caller compatible quantities are abstract, not verified biological data.
"""
SCOPE='caller input-uptake-loss nutrient ledger only; no aquaponics advice'


def balances(rows):
    """Exactlist/tuple1..64 quads(label,input,uptake,loss);printable Unicode
    exactstr labels1..40,repeats aggregate;exactint quantities0..1000000.
    Sorted(label,input sum,uptake sum,loss sum,signed residual),total residual
    and strictly negative residual labels. Negative values retained.
    Mixedrows accepted;no species,chemistry,stock carryover or units inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,quantity,uptake,loss=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(quantity) is not int or type(uptake) is not int or type(loss) is not int or not 0<=quantity<=1000000 or not 0<=uptake<=1000000 or not 0<=loss<=1000000:raise ValueError('quantities must be exactint0..1000000')
        q,u,l=groups.get(label,(0,0,0));groups[label]=(q+quantity,u+uptake,l+loss)
    result=tuple((label,q,u,l,q-u-l) for label,(q,u,l) in sorted(groups.items()))
    return {'balances':result,'total_residual':sum(row[4] for row in result),'negative':tuple(row[0] for row in result if row[4]<0),'scope':SCOPE}

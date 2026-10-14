"""Life Cycle Assessment.

PARTIAL: caller stage quantity/signed-factor ledger only, not life cycle
assessment, boundary validation, inventory verification or impact certification.
Caller factors are abstract, not verified environmental characterization data.
"""
SCOPE='caller stage quantity-signed-factor ledger only; no life cycle assessment claims'


def terms(rows):
    """Exactlist/tuple1..64 triples(label,quantity,factor);printable Unicode
    exactstr labels1..40,repeats aggregate;quantity exactint0..1000000,
    factor exactint-1000000..1000000. Sorted(label,total quantity,sum quantity
    *factor),total signed value and negative-value labels. Mixedrows accepted.
    Negative factors are caller arithmetic,not validated avoided burdens.
    No functional unit,system boundaries,units or actual impacts inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,quantity,factor=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(quantity) is not int or type(factor) is not int or not 0<=quantity<=1000000 or not -1000000<=factor<=1000000:raise ValueError('quantity must be exactint0..1000000 and factor exactint-1000000..1000000')
        old_quantity,old_value=groups.get(label,(0,0));groups[label]=(old_quantity+quantity,old_value+quantity*factor)
    result=tuple((label,quantity,value) for label,(quantity,value) in sorted(groups.items()))
    return {'terms':result,'total':sum(row[2] for row in result),'negative':tuple(row[0] for row in result if row[2]<0),'scope':SCOPE}

"""Green Chemistry.

PARTIAL: caller input/product/waste mass arithmetic only, not green chemistry,
reaction design, chemical safety, atom economy or environmental assessment.
Caller masses are abstract compatible units, not verified reaction data.
"""
from fractions import Fraction
SCOPE='caller input-product-waste mass arithmetic only; no green chemistry or safety claims'


def masses(rows):
    """Exactlist/tuple1..64 triples(label,input,product);unique printable Unicode
    exactstr labels1..40;exactint1<=product<=input<=1000000. Sorted(label,waste,
    waste/product),total waste and aggregate waste/product ratio. Mixedrows
    accepted;input-product is caller arithmetic,not inferred chemical balance.
    No solvents,catalysts,stoichiometry,hazards or chemical recommendations.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[];total_input=0;total_product=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,quantity,product=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(quantity) is not int or type(product) is not int or not 1<=product<=quantity<=1000000:raise ValueError('masses must be exactint1<=product<=input<=1000000')
        total_input+=quantity;total_product+=product;parsed.append((label,quantity-product,Fraction(quantity-product,product)))
    return {'masses':tuple(sorted(parsed,key=lambda row:row[0])),'total_waste':total_input-total_product,'aggregate_ratio':Fraction(total_input-total_product,total_product),'scope':SCOPE}

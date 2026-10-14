"""Biochar.

PARTIAL: caller feedstock/product mass-ratio arithmetic only, not biochar,
pyrolysis chemistry,carbon stability,soil benefit or process safety.
Masses caller declarations in matching units,not verified production data.
"""
from fractions import Fraction
SCOPE='caller feedstock-product mass ratios only; no biochar stability or soil claims'


def yield_ratio(rows):
    """Exactlist/tuple1..64 rows(label,feed,product),unique printable Unicode
    exactstr1..40;feed exactint1..1000000,product exactint0..feed. Return sorted
    (label,exact product/feed,remainder feed-product),total feed/product and
    aggregate ratio. No inferred composition,process emissions,energy or safety.
    Mixedrows accepted;remainder only bookkeeping,not a chemical product model.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[];feed_total=0;product_total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,feed,product=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(feed) is not int or type(product) is not int or not 1<=feed<=1000000 or not 0<=product<=feed:raise ValueError('masses must be exactint1<=feed<=1000000 and0<=product<=feed')
        result.append((label,Fraction(product,feed),feed-product));feed_total+=feed;product_total+=product
    return {'yields':tuple(sorted(result,key=lambda row:row[0])),'feed_total':feed_total,'product_total':product_total,
            'aggregate_ratio':Fraction(product_total,feed_total),'scope':SCOPE}

"""Desalination.

PARTIAL: caller feed/product quantity partition only, not desalination,
membrane performance, salt removal, drinking-water safety or plant design.
Caller compatible units and product quantities are not verified process data.
"""
from fractions import Fraction
SCOPE='caller feed-product partition arithmetic only; no desalination performance claims'


def partition(rows):
    """Exactlist/tuple1..64 triples(label,feed,product);unique printable Unicode
    exactstr labels1..40;exactint0<=product<=feed<=1000000. Sorted(label,
    remainder,product/feed or None at zero feed),total feed,product,remainder
    and aggregate recovery fraction. Mixedrows accepted. No salt,mass-density,
    energy,efficiency,cost or discharge assumptions inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[];total_feed=0;total_product=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,feed,product=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(feed) is not int or type(product) is not int or not 0<=product<=feed<=1000000:raise ValueError('quantities must be exactint0<=product<=feed<=1000000')
        total_feed+=feed;total_product+=product;parsed.append((label,feed-product,Fraction(product,feed) if feed else None))
    return {'partition':tuple(sorted(parsed,key=lambda row:row[0])),'feed':total_feed,'product':total_product,'remainder':total_feed-total_product,'recovery_fraction':Fraction(total_product,total_feed) if total_feed else None,'scope':SCOPE}

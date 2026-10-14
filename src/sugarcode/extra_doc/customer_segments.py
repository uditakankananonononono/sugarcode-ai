"""Row 366 Customer Segment Identification: exact grouping of supplied customer records.

Customers are (id, {attribute: value}) records the caller already holds. Customers
who share the same values on the chosen attributes form one segment. Segments are
listed by size (largest first, first appearance on ties) with member ids and exact
shares of all customers; segments with at least min_size members are marked
qualifying and their combined share is reported. 1 to 40 customers, 1 to 4
attributes, values are strings of 1 to 40 characters, ids and attribute names are
1 to 40 character strings, customer ids unique, min_size an int 1 to 40.
Caps are implementation choices, not spec values. Nothing is collected from any
source and no login or scraped data is used; all records are caller-supplied.
NOT_CLAIMED: that the records are accurate, lawfully obtained or representative,
market size, target-market choice, demand, willingness to pay, causal or
behavioral differences between segments, legal or approval-gate clearance,
deployment.
"""
from fractions import Fraction

NOT_CLAIMED = ('records are accurate, lawful or representative', 'market size', 'target-market choice',
               'demand', 'willingness to pay', 'behavioral differences between segments',
               'legal or approval-gate clearance', 'deployment')


def _s(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be str')
    if not 1 <= len(v) <= 40:
        raise ValueError(what + ' must be 1 to 40 characters')
    return v


def identify_segments(customers, attributes, min_size=1):
    if type(customers) not in (list, tuple) or type(attributes) not in (list, tuple):
        raise TypeError('customers and attributes must be lists or tuples')
    if not 1 <= len(customers) <= 40:
        raise ValueError('customer count must be between 1 and 40')
    if not 1 <= len(attributes) <= 4:
        raise ValueError('attribute count must be between 1 and 4')
    if type(min_size) is not int:
        raise TypeError('min_size must be nonbool int')
    if not 1 <= min_size <= 40:
        raise ValueError('min_size must be between 1 and 40')
    attrs = [_s(a, 'attribute names') for a in attributes]
    if len(set(attrs)) != len(attrs):
        raise ValueError('attribute names must be unique')
    rows = []
    for c in customers:
        if type(c) not in (list, tuple) or len(c) != 2:
            raise ValueError('each customer must be (id, attributes)')
        if type(c[1]) is not dict:
            raise TypeError('customer attributes must be a dict')
        cid = _s(c[0], 'customer ids')
        missing = [a for a in attrs if a not in c[1]]
        if missing:
            raise ValueError('customer is missing attribute ' + missing[0])
        rows.append((cid, tuple(_s(c[1][a], 'attribute values') for a in attrs)))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('customer ids must be unique')
    groups = {}
    for cid, key in rows:
        groups.setdefault(key, []).append(cid)
    order = sorted(range(len(groups)), key=lambda i: (-len(list(groups.values())[i]), i))
    keys = list(groups)
    n = len(rows)
    segments = []
    for i in order:
        members = groups[keys[i]]
        segments.append({'attributes': dict(zip(attrs, keys[i])), 'members': list(members),
                         'size': len(members), 'share': Fraction(len(members), n),
                         'qualifying': len(members) >= min_size})
    q = sum(s['size'] for s in segments if s['qualifying'])
    return {'segments': segments, 'segment_count': len(segments),
            'qualifying_count': sum(1 for s in segments if s['qualifying']),
            'qualifying_share': Fraction(q, n), 'customer_count': n,
            'target_market_validated': False, 'not_claimed': NOT_CLAIMED}

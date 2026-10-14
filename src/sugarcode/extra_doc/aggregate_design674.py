"""Doc row674 Aggregate Design: PARTIAL offline atomic write-boundary audit.

owners exact dict1..50 entity IDs to aggregate IDs, transactions exact list0..100
of exact lists1..50 distinct known entity IDs. Labels nonblank exact str<=80.
Report input transaction indexes touching more than one supplied aggregate and
sorted aggregate IDs per transaction. No inferred consistency or database writes.
"""


def audit(owners, transactions):
    if type(owners) is not dict or not 1<=len(owners)<=50:
        raise ValueError('owners must be an exact dict with 1..50 entries')
    if any(type(x) is not str or not 1<=len(x)<=80 or not x.strip() for pair in owners.items() for x in pair):
        raise ValueError('IDs must be nonblank exact strings of 1..80 characters')
    if type(transactions) is not list or len(transactions)>100:
        raise ValueError('transactions must be an exact list with 0..100 entries')
    for row in transactions:
        if type(row) is not list or not 1<=len(row)<=50:
            raise ValueError('transaction must be an exact list with 1..50 entities')
        if any(type(x) is not str or x not in owners for x in row) or len(set(row))!=len(row):
            raise ValueError('transaction entities must be distinct exact known IDs')
    groups=[sorted({owners[x] for x in row}) for row in transactions]
    return {'aggregate_sets':groups,'cross_boundary':[i for i,g in enumerate(groups) if len(g)>1],
            'claim':'PARTIAL','consistency_validated':False}

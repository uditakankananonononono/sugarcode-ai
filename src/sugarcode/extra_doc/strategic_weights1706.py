"""Strategic Environmental Assessment.

PARTIAL: caller alternative/criterion weighted-score ledger only, not a
strategic environmental assessment, policy evaluation or decision advice.
Caller weights and scores are abstract, not validated environmental evidence.
"""
SCOPE='caller alternative-criterion weighted-score ledger only; no strategic environmental assessment'


def scores(rows):
    """Exactlist/tuple1..64 quads(alternative,criterion,weight,score);printable
    Unicode exactstr endpoints1..40;unique alternative/criterion pairs;
    exactint weights,scores0..1000000. Sorted alternative totals and sorted
    (alternative,criterion,product) terms. No ranking or recommended choice.
    Mixedrows accepted;no normalized weights,comparability or outcomes inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    seen=set();terms=[];groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        alternative,criterion,weight,score=row
        if type(alternative) is not str or not 1<=len(alternative)<=40 or not all(ch.isprintable() for ch in alternative):raise ValueError('alternative must be exactstr printable Unicode length1..40')
        if type(criterion) is not str or not 1<=len(criterion)<=40 or not all(ch.isprintable() for ch in criterion):raise ValueError('criterion must be exactstr printable Unicode length1..40')
        key=(alternative,criterion)
        if key in seen:raise ValueError('alternative/criterion pairs must be unique')
        seen.add(key)
        if type(weight) is not int or type(score) is not int or not 0<=weight<=1000000 or not 0<=score<=1000000:raise ValueError('weights and scores must be exactint0..1000000')
        value=weight*score;terms.append((alternative,criterion,value));groups[alternative]=groups.get(alternative,0)+value
    return {'terms':tuple(sorted(terms)),'totals':tuple(sorted(groups.items())),'scope':SCOPE}

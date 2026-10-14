"""Row 361 Competitive Analysis: supplied criteria competitor strength map.

For each supplied competitor/criterion pair, compare score against a supplied
baseline. Weighted delta totals measure relative position, not factual quality.
Weighted delta is not normalized by weight sum; ranking ties use lower index.
Caps 16 competitors, 16 criteria; scores/weights 0..1000 integers.
NOT_CLAIMED: external competitor research, truthful scores, strategic advice,
market performance prediction or actual competitive advantage.
"""


def competitive_map(scores,baseline,weights):
    if any(type(v) not in (list,tuple) for v in (scores,baseline,weights)):
        raise TypeError('inputs must be lists or tuples')
    if not 1<=len(scores)<=16 or not 1<=len(baseline)<=16:
        raise ValueError('competitor and criterion counts must be between 1 and 16')
    n=len(baseline)
    if len(weights)!=n or any(type(row) not in (list,tuple) or len(row)!=n for row in scores):
        raise ValueError('criterion shapes must agree')
    for values in [baseline,weights,*scores]:
        if any(type(v) is not int or not 0<=v<=1000 for v in values):
            raise ValueError('scores and weights must be nonbool integers zero through 1000')
    if sum(weights)==0:raise ValueError('at least one weight must be positive')
    rows=[]
    for row in scores:
        deltas=[v-b for v,b in zip(row,baseline)]
        rows.append({'strengths':[i for i,d in enumerate(deltas) if d>0],
                     'weaknesses':[i for i,d in enumerate(deltas) if d<0],
                     'parity':[i for i,d in enumerate(deltas) if d==0],
                     'weighted_delta':sum(d*w for d,w in zip(deltas,weights))})
    ranking=sorted(range(len(rows)),key=lambda i:(-rows[i]['weighted_delta'],i))
    return {'competitors':rows,'ranking':ranking,'scores_verified':False}

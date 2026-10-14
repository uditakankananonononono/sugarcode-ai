"""Row 369 Pain Point Discovery: supplied unmet-need severity/frequency map.

Priority=severity*frequency*(100-satisfaction). Returns positive unmet needs
ranked by descending priority then input index, and satisfied/zero-impact needs.
Caps 64 needs, integer ratings0..100; no strings or user evidence inferred.
NOT_CLAIMED: customer research, discovering unreported needs, verified ratings,
causal pain diagnosis, actionable product fit or real-world validation.
"""


def discover_pain(needs):
    if type(needs) not in (list,tuple):raise TypeError('needs must be a list or tuple')
    if not 1<=len(needs)<=64:raise ValueError('need count must be between 1 and 64')
    if any(type(row) not in (list,tuple) or len(row)!=3 for row in needs):
        raise ValueError('needs must contain severity frequency satisfaction triples')
    if any(type(v) is not int or not 0<=v<=100 for row in needs for v in row):
        raise ValueError('ratings must be nonbool integers zero through 100')
    scores=[severity*frequency*(100-satisfaction) for severity,frequency,satisfaction in needs]
    ranking=sorted((i for i,s in enumerate(scores) if s>0),key=lambda i:(-scores[i],i))
    return {'priorities':scores,'unmet_need_indices':ranking,
            'zero_priority_indices':[i for i,s in enumerate(scores) if s==0],'needs_validated':False}

"""Doc row1743 Discourse Analysis: PARTIAL exact supplied lexical-marker audit.

Markers exact list1..20 unique exact nonblank strings<=80 with no whitespace.
Texts exact list1..100 exact strings0..1000, whitespace tokenization, case-sensitive
exact-token matching. Return per-text marker counts and total frequencies, in
marker order. No stance, meaning, pragmatic intent, discourse or speaker inference.
"""


def audit_markers(markers,texts):
    if type(markers) is not list or not 1<=len(markers)<=20 or any(type(m) is not str or not 1<=len(m)<=80 or any(c.isspace() for c in m) for m in markers) or len(set(markers))!=len(markers):
        raise ValueError('markers must be an exact list of 1..20 unique nonwhitespace tokens of 1..80 characters')
    if type(texts) is not list or not 1<=len(texts)<=100 or any(type(t) is not str or len(t)>1000 for t in texts):
        raise ValueError('texts must be an exact list of 1..100 exact strings of 0..1000 characters')
    counts=[[t.split().count(m) for m in markers] for t in texts]
    totals=[(m,sum(row[i] for row in counts)) for i,m in enumerate(markers)]
    return {'counts':counts,'totals':totals,'claim':'PARTIAL','discourse_validated':False}

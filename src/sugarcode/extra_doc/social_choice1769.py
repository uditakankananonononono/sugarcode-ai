"""Doc row1769 Social Choice: PARTIAL exact ranked-ballot pairwise fixture.

Candidates exact list2..10 unique nonblank exact str1..80. Ballots exact list1..100
exact candidate permutations. Return ordered pair preference counts and strict
Condorcet winners (none for ties/cycles). No real social welfare or election claim.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def compare(candidates,ballots):
    if type(candidates) is not list or not 2<=len(candidates)<=10 or any(not _label(x) for x in candidates) or len(set(candidates))!=len(candidates):raise ValueError('candidates must be an exact list of 2..10 unique valid labels')
    if type(ballots) is not list or not 1<=len(ballots)<=100:raise ValueError('ballots must be an exact list with 1..100 entries')
    for b in ballots:
        if type(b) is not list or len(b)!=len(candidates) or any(not _label(x) for x in b) or len(set(b))!=len(b) or set(b)!=set(candidates):raise ValueError('each ballot must be an exact candidate permutation list')
    counts={(a,b):sum(row.index(a)<row.index(b) for row in ballots) for a in candidates for b in candidates if a!=b}
    winners=[a for a in candidates if all(counts[(a,b)]>counts[(b,a)] for b in candidates if a!=b)]
    return {'pairwise':[(a,b,n) for (a,b),n in counts.items()],'winners':winners,'claim':'PARTIAL','welfare_validated':False}

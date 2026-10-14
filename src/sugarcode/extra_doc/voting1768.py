"""Doc row1768 Voting Theory: PARTIAL exact ranked-ballot Borda fixture.

Candidates exact list2..10 unique nonblank exact str1..80. Ballots exact list1..100
exact lists, each a permutation of candidates. Return Borda scores (n-1 down0),
all leaders in supplied candidate order. No real election or welfare validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def tally(candidates,ballots):
    if type(candidates) is not list or not 2<=len(candidates)<=10 or any(not _label(x) for x in candidates) or len(set(candidates))!=len(candidates):raise ValueError('candidates must be an exact list of 2..10 unique valid labels')
    if type(ballots) is not list or not 1<=len(ballots)<=100:raise ValueError('ballots must be an exact list with 1..100 entries')
    for b in ballots:
        if type(b) is not list or len(b)!=len(candidates) or any(not _label(x) for x in b) or len(set(b))!=len(b) or set(b)!=set(candidates):raise ValueError('each ballot must be an exact candidate permutation list')
    scores=[(c,sum(len(candidates)-1-b.index(c) for b in ballots)) for c in candidates];best=max(s for c,s in scores)
    return {'scores':scores,'leaders':[c for c,s in scores if s==best],'claim':'PARTIAL','election_validated':False}

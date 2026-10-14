"""Doc row1763 Public Choice: PARTIAL supplied policy approval tally.

Policies exact list2..20 unique valid labels. Ballots exact list1..100 tuples
(id,approvals), unique IDs, approvals exact list0..20 unique known policies.
Labels exact nonblank str1..80. Return approval counts and all top policies
in policy order (all tie when ballots empty approvals). No actual public choice,
welfare, preference, election or democratic validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def tally(policies,ballots):
    if type(policies) is not list or not 2<=len(policies)<=20 or any(not _label(x) for x in policies) or len(set(policies))!=len(policies):raise ValueError('policies must be an exact list of 2..20 unique valid labels')
    if type(ballots) is not list or not 1<=len(ballots)<=100:raise ValueError('ballots must be an exact list with 1..100 entries')
    ids=set()
    for row in ballots:
        if type(row) is not tuple or len(row)!=2:raise ValueError('ballot must be an id approvals tuple')
        n,approvals=row
        if not _label(n) or n in ids:raise ValueError('ballot IDs must be unique valid labels')
        ids.add(n)
        if type(approvals) is not list or len(approvals)>20 or any(not _label(x) or x not in policies for x in approvals) or len(set(approvals))!=len(approvals):raise ValueError('approvals must be an exact list of 0..20 unique known policy labels')
    counts=[(p,sum(p in a for n,a in ballots)) for p in policies];high=max(c for p,c in counts)
    return {'counts':counts,'leaders':[p for p,c in counts if c==high],'claim':'PARTIAL','election_validated':False}

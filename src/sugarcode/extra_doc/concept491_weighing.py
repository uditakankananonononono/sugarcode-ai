"""Finite counterfeit-coin hypothesis fixtures, not physical weighing advice.

n exact int1..6. Hypothesis exact tuple(coin0..n-1,sign-1or1), where sign
is light/heavy. Weighing exact tuple lengthn of -1,0,1; equal nonzero counts
of -1/+1, no coin on both pans. Empty pans allowed. Outcome -1,0,1 is
signed weight difference assuming every genuine coin has identical weight.
Candidates exact tuple<=12 unique hypotheses; menu exact tuple<=6 unique
weighings. Transcript exact tuple<=8 (weighing,outcome) pairs; repeats allowed.
All shape/type checks precede ranges and duplicates within each validator;
public parameter validation order is n,candidates,menu/transcript,scalars.
No external data, physical calibration, error distribution or optimality
outside the caller's finite menu is inferred.
"""
from itertools import combinations
from functools import lru_cache
SCOPE = 'PARTIAL exact finite balance-scale hypothesis discrimination'
NOT_CLAIMED = ('AGI-like intelligence','physical weighing validity','global strategy optimality','production readiness')
CLAIMS = {'agi_like_intelligence':False,'physical_validity':False,'production_ready':False}


def _fail(code):
    raise ValueError('W491:'+code)


def _integer(value,label,lo,hi):
    if type(value) is not int:_fail('type:'+label)
    if not lo<=value<=hi:_fail('bound:'+label)


def _n(n):
    _integer(n,'n',1,6)


def _hypotheses(n,hs):
    if type(hs) is not tuple:_fail('type:hypotheses')
    if len(hs)>12:_fail('length:hypotheses')
    if any(type(h)is not tuple or len(h)!=2 for h in hs):_fail('shape:hypothesis')
    if any(type(x)is not int for h in hs for x in h):_fail('type:hypothesis:entry')
    if any(not 0<=coin<n or sign not in (-1,1) for coin,sign in hs):_fail('bound:hypothesis:entry')
    if len(set(hs))!=len(hs):_fail('duplicate:hypothesis')


def _weighings(n,ws,cap,label):
    if type(ws)is not tuple:_fail('type:'+label)
    if len(ws)>cap:_fail('length:'+label)
    if any(type(w)is not tuple or len(w)!=n for w in ws):_fail('shape:weighing')
    if any(type(x)is not int for w in ws for x in w):_fail('type:weighing:entry')
    if any(x not in (-1,0,1) for w in ws for x in w):_fail('bound:weighing:entry')
    if any(sum(w)!=0 for w in ws):_fail('unbalanced:pans')


def _menu(n,menu):
    _weighings(n,menu,6,'menu')
    if len(set(menu))!=len(menu):_fail('duplicate:weighing')


def _transcript(n,transcript):
    if type(transcript)is not tuple:_fail('type:transcript')
    if len(transcript)>8:_fail('length:transcript')
    if any(type(r)is not tuple or len(r)!=2 for r in transcript):_fail('shape:transcript:row')
    _weighings(n,tuple(w for w,_ in transcript),8,'transcript:weighings')
    if any(type(o)is not int for _,o in transcript):_fail('type:outcome')
    if any(o not in (-1,0,1) for _,o in transcript):_fail('bound:outcome')


def _partition(hs,w):
    return tuple(tuple(h for h in hs if w[h[0]]*h[1]==outcome) for outcome in (-1,0,1))


def weighing_outcome(n,hypothesis,weighing):
    _n(n);_hypotheses(n,(hypothesis,));_weighings(n,(weighing,),1,'weighing')
    return weighing[hypothesis[0]]*hypothesis[1]


def hypothesis_partition(n,candidates,weighing):
    """Three ordered buckets(-1,0,+1), preserve caller hypothesis order."""
    _n(n);_hypotheses(n,candidates);_weighings(n,(weighing,),1,'weighing')
    return _partition(candidates,weighing)


def consistent_hypotheses(n,candidates,transcript):
    _n(n);_hypotheses(n,candidates);_transcript(n,transcript)
    return tuple(h for h in candidates if all(w[h[0]]*h[1]==o for w,o in transcript))


def transcript_consistent(n,transcript):
    """Whether any of all2n heavy/light hypotheses fits the transcript."""
    _n(n);_transcript(n,transcript)
    for coin in range(n):
        for sign in (-1,1):
            if all(w[coin]*sign==o for w,o in transcript):return True
    return False


def weighing_information_profile(n,candidates,weighing):
    """Return(bucket sizes,worst remaining size,sum squared sizes).

    Sum squared sizes is the integer numerator of uniform expected ambiguity.
    """
    _n(n);_hypotheses(n,candidates);_weighings(n,(weighing,),1,'weighing')
    sizes=tuple(len(bucket) for bucket in _partition(candidates,weighing))
    return sizes,max(sizes),sum(s*s for s in sizes)


def best_weighings(n,candidates,menu):
    """Indices minimizing(worst bucket,sum squared buckets),ties retained."""
    _n(n);_hypotheses(n,candidates);_menu(n,menu)
    scores=[]
    for w in menu:
        counts=[len(bucket) for bucket in _partition(candidates,w)]
        scores.append((max(counts),sum(x*x for x in counts)))
    return tuple(i for i,score in enumerate(scores) if score==min(scores))


def indistinguishable_pairs(n,candidates,menu):
    """Hypothesis-index pairs with identical outcome words over supplied menu."""
    _n(n);_hypotheses(n,candidates);_menu(n,menu)
    words=[tuple(w[c]*s for w in menu) for c,s in candidates]
    return tuple((i,j) for i,j in combinations(range(len(candidates)),2) if words[i]==words[j])


def minimum_nonadaptive_tests(n,candidates,menu):
    """All minimum-cardinality menu-index subsets separating candidates.

    None if impossible; ((),) for at most1 candidate. At most64 subsets.
    """
    _n(n);_hypotheses(n,candidates);_menu(n,menu)
    for size in range(len(menu)+1):
        found=[]
        for indices in combinations(range(len(menu)),size):
            words=[tuple(menu[i][c]*s for i in indices) for c,s in candidates]
            if len(set(words))==len(candidates):found.append(indices)
        if found:return tuple(found)
    return None


def robust_hypotheses(n,candidates,transcript,error_budget):
    """Hypotheses with at most budget0..8 mismatched supplied outcomes."""
    _n(n);_hypotheses(n,candidates);_transcript(n,transcript)
    _integer(error_budget,'error_budget',0,8)
    return tuple(h for h in candidates if sum(w[h[0]]*h[1]!=o for w,o in transcript)<=error_budget)


def adaptive_depth_certificate(n,candidates,menu,depth):
    """Depth0..3 feasibility and canonical finite-menu decision certificate.

    None for impossible. Leaf is ('leaf', hypothesis) or ('leaf',None) for
    unreachable empty bucket. Branch is ('test',menu_index,three child tuples
    in -1,0,+1 order). First feasible menu index at each node wins. Tests may
    be reused, but non-splitting tests are skipped. At most40 nodes.
    """
    _n(n);_hypotheses(n,candidates);_menu(n,menu);_integer(depth,'depth',0,3)
    @lru_cache(None)
    def solve(hs,left):
        if len(hs)<=1:return ('leaf',hs[0] if hs else None)
        if not left:return None
        if len(hs)>3**left:return None
        for i,w in enumerate(menu):
            buckets=_partition(hs,w)
            if max(map(len,buckets))==len(hs):continue
            children=tuple(solve(bucket,left-1) for bucket in buckets)
            if all(child is not None for child in children):return ('test',i,children)
        return None
    return solve(candidates,depth)

"""Row 288 Information Architecture: exact bounded navigation-tree generation.

Chooses a parent for each supplied content node from finite allowed choices,
rejects cycles, and minimizes weighted click-depth from an external root -1.
One coherent rooted navigation tree is generated, with explicit node depths.
Caps: 1..6 nodes and 1..4 parent options per node. Equal-cost ties retain
the first feasible tuple in supplied product order.
NOT_CLAIMED: semantic content grouping, discoverability validation, intuitive
labels, universal organization quality, visual sitemap, or deployment.
"""
from fractions import Fraction
from itertools import product


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('weights must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('weights must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('weights must fit 32 bits')
    return Fraction(v)


def organize_navigation(weights,parent_options):
    if type(weights) not in (list,tuple) or type(parent_options) not in (list,tuple):
        raise TypeError('inputs must be lists or tuples')
    n=len(weights)
    if not 1<=n<=6:raise ValueError('node count must be between 1 and 6')
    if len(parent_options)!=n:raise ValueError('parent options must match node count')
    for options in parent_options:
        if type(options) not in (list,tuple) or not 1<=len(options)<=4:
            raise ValueError('each node must have between 1 and 4 parent options')
    for i,options in enumerate(parent_options):
        if any(type(p) is not int or not -1<=p<n or p==i for p in options):
            raise ValueError('parents must be nonbool indices or root -1 and not self')
        if len(set(options))!=len(options):raise ValueError('parent options must be unique')
    w=[_number(v) for v in weights]
    if any(v<0 for v in w):raise ValueError('weights must be nonnegative')
    best=None;feasible=0;candidates=0
    for parents in product(*parent_options):
        candidates+=1;depths=[]
        for i in range(n):
            seen=set();cursor=i;depth=0
            while cursor!=-1 and cursor not in seen:
                seen.add(cursor);cursor=parents[cursor];depth+=1
            if cursor!=-1:break
            depths.append(depth)
        if len(depths)!=n:continue
        feasible+=1;cost=sum((v*d for v,d in zip(w,depths)),Fraction(0))
        if best is None or cost<best[0]:best=(cost,parents,depths)
    if best is None:raise ValueError('no acyclic rooted navigation exists')
    cost,parents,depths=best
    return {'parents':list(parents),'depths':depths,'weighted_depth':cost,
            'candidate_count':candidates,'feasible_tree_count':feasible,'discoverability_validated':False}

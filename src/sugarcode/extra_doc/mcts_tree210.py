"""UCT Monte Carlo tree search on a supplied bounded decision tree.
NOT_CLAIMED: true environment model; global optimum at finite budget; unbiased
rollout policy; exact UCT transcendental scores; external or runtime execution.
"""
import math
from fractions import Fraction


def search(nodes,root,iterations,exploration,draws):
    if type(iterations) is not int or not 1<=iterations<=100:raise ValueError('strict MCTS iterations 1..100')
    if type(exploration) not in (int,float) or not 0<=exploration<=10 or not math.isfinite(exploration):raise ValueError('strict finite exploration 0..10')
    if type(nodes) is not list or not 1<=len(nodes)<=100:raise ValueError('1..100 tree nodes before scan')
    if type(draws) is not list or len(draws)!=iterations*8:raise ValueError('exact iterations times 8 rollout draws before scan')
    if any(type(v) not in (int,float) or not 0<=v<1 or not math.isfinite(v) for v in draws):raise ValueError('strict finite rollout draws [0,1)')
    tree={};parents={}
    for n in nodes:
        if type(n) is not dict or set(n)!={'id','children','reward'}:raise ValueError('exact tree id/children/reward fields')
        ident=n['id'];children=n['children'];reward=n['reward']
        if type(ident) is not str or not 1<=len(ident)<=80 or ident in tree:raise ValueError('unique tree id 1..80 chars')
        if type(children) is not list or len(children)>8 or any(type(c) is not str for c in children) or len(set(children))!=len(children):raise ValueError('0..8 distinct child ids')
        if children:
            if reward is not None:raise ValueError('internal reward must be None')
        elif type(reward) not in (int,float) or not -1000<=reward<=1000 or not math.isfinite(reward):raise ValueError('strict finite terminal reward within -1000..1000')
        tree[ident]=(children[:],None if children else Fraction(str(reward)))
        for c in children:
            if c in parents:raise ValueError('one parent per nonroot node')
            parents[c]=ident
    if type(root) is not str or root not in tree or root in parents:raise ValueError('existing parentless root required')
    reached=set()
    def validate(node,depth):
        if depth>8:raise ValueError('tree depth at most 8 edges')
        if node not in tree or node in reached:raise ValueError('existing acyclic connected tree required')
        reached.add(node)
        for child in tree[node][0]:validate(child,depth+1)
    validate(root,0)
    if len(reached)!=len(tree):raise ValueError('existing acyclic connected tree required')
    visits={n:0 for n in tree};sums={n:Fraction(0) for n in tree};expanded={n:[] for n in tree};trace=[]
    for t in range(iterations):
        path=[root];node=root
        while tree[node][0]:
            untried=[c for c in tree[node][0] if c not in expanded[node]]
            if untried:
                child=untried[0];expanded[node].append(child);node=child;path.append(node);break
            def uct(c):return float(sums[c]/visits[c])+exploration*math.sqrt(math.log(visits[node])/visits[c])
            node=max(expanded[node],key=lambda c:(uct(c),-tree[path[-1]][0].index(c)));path.append(node)
        rollout=node;rollout_path=[node];k=0
        while tree[rollout][0]:
            menu=tree[rollout][0];draw=draws[t*8+k];rollout=menu[min(int(draw*len(menu)),len(menu)-1)];rollout_path.append(rollout);k+=1
        reward=tree[rollout][1]
        for n in path:visits[n]+=1;sums[n]+=reward
        trace.append({'iteration':t+1,'selected_path':path,'rollout_path':rollout_path,'reward_fraction':str(reward)})
    options=expanded[root]
    selected=max(options,key=lambda c:(visits[c],sums[c]/visits[c],-tree[root][0].index(c))) if options else None
    return {'selected_root_child':selected,'visits':visits,'reward_sum_fraction':{n:str(v) for n,v in sums.items()},'trace':trace,
            'selection':'most visits, then highest mean, then supplied child order','uct_scores_FLOAT':True,'external_effects':[]}

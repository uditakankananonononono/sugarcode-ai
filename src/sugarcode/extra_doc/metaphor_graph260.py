"""Generate new relational metaphors by exact small-graph analogy search.
NOT_CLAIMED: universal novelty; semantic truth; reader illumination; literary
quality; model creativity benchmark; publishing or runtime integration.
"""
from itertools import permutations
import unicodedata


def generate(target,sources,previous):
    def text(s):
        if type(s) is not str or not 1<=len(s)<=80 or s!=s.strip() or any(unicodedata.category(c).startswith('C') or c in '\n\r\t' for c in s):raise ValueError('strict visible trimmed text 1..80 characters')
        return s
    def graph(g):
        if type(g) is not dict or set(g)!={'domain','nodes','edges'}:raise ValueError('exact domain/nodes/edges graph fields')
        domain=text(g['domain']);nodes=g['nodes'];edges=g['edges']
        if type(nodes) is not list or not 2<=len(nodes)<=4:raise ValueError('2..4 graph nodes before scan')
        nodes=[text(s) for s in nodes]
        if len(set(nodes))!=len(nodes):raise ValueError('unique graph nodes')
        if type(edges) is not list or not 1<=len(edges)<=12:raise ValueError('1..12 relational edges before scan')
        triples=[]
        for row in edges:
            if type(row) is not list or len(row)!=3:raise ValueError('edge source/relation/destination triple')
            triple=tuple(text(s) for s in row)
            if triple[0] not in nodes or triple[2] not in nodes or triple[0]==triple[2]:raise ValueError('distinct graph endpoints in node menu')
            if triple in triples:raise ValueError('unique relational edges')
            triples.append(triple)
        return domain,nodes,triples
    td,tn,te=graph(target)
    if type(sources) is not list or not 1<=len(sources)<=10:raise ValueError('1..10 source graphs before scan')
    parsed=[graph(g) for g in sources]
    if len({g[0] for g in parsed})!=len(parsed):raise ValueError('unique source domain names')
    if type(previous) is not list or len(previous)>50:raise ValueError('0..50 previously used domain pairings before scan')
    used=set()
    for row in previous:
        if type(row) is not list or len(row)!=2:raise ValueError('previous target/source domain pairs')
        used.add((text(row[0]),text(row[1])))
    candidates=[]
    for sd,sn,se in parsed:
        if sd==td or (td,sd) in used or len(tn)!=len(sn):continue
        best=None
        for perm in permutations(sn):
            mapping=dict(zip(tn,perm));matches=[e for e in te if (mapping[e[0]],e[1],mapping[e[2]]) in se]
            key=(-len(matches),tuple(perm))
            if best is None or key<best[0]:best=(key,mapping,matches)
        _,mapping,matches=best
        if not matches:continue
        mismatch=[e for e in te if e not in matches]
        clauses=[f'{a} is {mapping[a]}' for a in tn]
        explanations=[f'As {a} {r} {b}, {mapping[a]} {r} {mapping[b]}.' for a,r,b in matches]
        candidates.append({'source_domain':sd,'mapping':mapping,'metaphor':f'{td} is {sd}: '+ '; '.join(clauses)+'.',
                           'explanation':' '.join(explanations),'matched_edges':[list(e) for e in matches],
                           'unmapped_target_edges':[list(e) for e in mismatch],'matched_edge_count':len(matches),
                           'fresh_domain_pairing_in_supplied_history':True,'universal_novelty_claimed':False,'reader_illumination_verified':False})
    candidates.sort(key=lambda c:(-c['matched_edge_count'],c['source_domain']))
    return {'candidates':candidates,'status':'generated_relational_comparisons' if candidates else 'no_fresh_relational_match',
            'novelty_scope':'only absence of exact domain pair in supplied history','review_required':True,'external_effects':[]}

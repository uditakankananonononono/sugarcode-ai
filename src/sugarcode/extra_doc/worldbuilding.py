"""Row 264 Worldbuilding: finite coherent fictional-world generation.

Selects one supplied value per world dimension, enforcing supplied
implications and exclusions. Enumerates up to 4096 candidates and returns
first coherent assignment plus a count of all coherent universes and
per-rule truth certificates. This generates a world configuration, not a
lexical diagnostic.
NOT_CLAIMED: open-ended world invention, narrative or scientific realism,
originality, creative quality, prose generation, autonomous publication.
"""
from itertools import product


def _label(v):
    if type(v) is not str:raise TypeError('labels must be strings')
    if not 1<=len(v)<=80:raise ValueError('label length must be between 1 and 80')
    if not v.strip():raise ValueError('labels must not be blank')
    return v


def build_world(domains, implications, exclusions):
    if type(domains) is not dict:raise TypeError('domains must be a dict')
    if not 1<=len(domains)<=6:raise ValueError('dimension count must be between 1 and 6')
    if type(implications) not in (list,tuple) or type(exclusions) not in (list,tuple):
        raise TypeError('rule sets must be lists or tuples')
    if len(implications)>64 or len(exclusions)>64:
        raise ValueError('each rule set must not exceed 64 rules')
    count=1
    for vals in domains.values():
        if type(vals) not in (list,tuple) or not 1<=len(vals)<=4:
            raise ValueError('each domain must have between 1 and 4 values')
        count*=len(vals)
    if count>4096:raise ValueError('world search must not exceed 4096 candidates')
    for rule in list(implications)+list(exclusions):
        if type(rule) not in (list,tuple) or len(rule)!=4:raise ValueError('rules must have four fields')
    keys=[_label(k) for k in domains]
    options=[[_label(v) for v in domains[k]] for k in keys]
    if any(len(set(vals))!=len(vals) for vals in options):raise ValueError('domain values must be unique')
    imps=[tuple(_label(v) for v in r) for r in implications]
    excls=[tuple(_label(v) for v in r) for r in exclusions]
    for a,x,b,y in imps+excls:
        if a not in domains or b not in domains or x not in domains[a] or y not in domains[b]:
            raise ValueError('rules must reference known dimensions and values')
    first=None;coherent=0
    for values in product(*options):
        candidate=dict(zip(keys,values))
        implication_truth=[candidate[a]!=x or candidate[b]==y for a,x,b,y in imps]
        exclusion_truth=[not(candidate[a]==x and candidate[b]==y) for a,x,b,y in excls]
        if all(implication_truth) and all(exclusion_truth):
            coherent+=1
            if first is None:first=(candidate,implication_truth,exclusion_truth)
    if first is None:raise ValueError('no coherent world exists')
    world,it,et=first
    return {'world':world,'coherent_world_count':coherent,'candidate_count':count,
            'implication_certificate':it,'exclusion_certificate':et,'creative_quality_claimed':False}

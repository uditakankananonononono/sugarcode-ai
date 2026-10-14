"""Row1984 Automated Reasoning: synchronous propositional Horn closure.
Facts exact list0..20 unique nonblank exact str1..80 atoms. Rules exact list0..40
of exact (premises,conclusion) tuples;premises exact list0..10 unique valid atoms,
conclusion valid atom. Query valid atom. Each round derives all new conclusions
whose premises were known before the round,with input-rule order deduplication.
Return closure ordered by fact/first derivation,rounds,and query entailment.
Finite monotonic Horn model only;does not infer general natural-language truth.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def infer(facts,rules,query):
    if type(facts) is not list or len(facts)>20:raise ValueError('facts must be exact list0..20')
    seen=set()
    for x in facts:
        if not _label(x) or x in seen:raise ValueError('facts must be unique valid atoms')
        seen.add(x)
    if type(rules) is not list or len(rules)>40:raise ValueError('rules must be exact list0..40')
    for row in rules:
        if type(row) is not tuple or len(row)!=2:raise ValueError('rule must be exact premises conclusion tuple')
        premises,c=row
        if type(premises) is not list or len(premises)>10:raise ValueError('premises must be exact list0..10')
        local=set()
        for x in premises:
            if not _label(x) or x in local:raise ValueError('premises must be unique valid atoms')
            local.add(x)
        if not _label(c):raise ValueError('conclusion must be valid atom')
    if not _label(query):raise ValueError('query must be valid atom')
    closure=list(facts);rounds=[]
    while True:
        new=[]
        for premises,c in rules:
            if c not in seen and c not in new and all(x in seen for x in premises):new.append(c)
        if not new:break
        rounds.append(new);closure.extend(new);seen.update(new)
    return {'closure':closure,'rounds':rounds,'entailed':query in seen,'general_truth_inferred':False}

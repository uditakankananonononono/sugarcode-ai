"""Doc row1761 Institutional Analysis: PARTIAL supplied rule compliance ledger.

Rules exact list1..20 unique valid labels; institutions exact list1..100 tuples
(id,observed_rules), unique IDs; observations exact list0..20 unique known rules.
Labels exact nonblank str1..80. Return missing supplied rules per institution
and observed count per rule. No real legal compliance or institutional inference.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_rules(rules,institutions):
    if type(rules) is not list or not 1<=len(rules)<=20 or any(not _label(x) for x in rules) or len(set(rules))!=len(rules):raise ValueError('rules must be an exact list of 1..20 unique valid labels')
    if type(institutions) is not list or not 1<=len(institutions)<=100:raise ValueError('institutions must be an exact list with 1..100 entries')
    ids=set()
    for row in institutions:
        if type(row) is not tuple or len(row)!=2:raise ValueError('institution must be an id observed_rules tuple')
        name,observed=row
        if not _label(name) or name in ids:raise ValueError('institution IDs must be unique valid labels')
        ids.add(name)
        if type(observed) is not list or len(observed)>20 or any(not _label(x) or x not in rules for x in observed) or len(set(observed))!=len(observed):raise ValueError('observed must be an exact list of 0..20 unique known rule labels')
    return {'missing':[(n,[r for r in rules if r not in observed]) for n,observed in institutions],'rule_counts':[(r,sum(r in observed for n,observed in institutions)) for r in rules],'claim':'PARTIAL','compliance_validated':False}

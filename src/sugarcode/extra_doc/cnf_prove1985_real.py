"""Row1985 Theorem Proving: exhaustive finite CNF literal entailment certificate.
Atoms exact list1..8 unique nonblank exact str1..80. Clauses exact list0..20,
each exact list0..8 of exact (atom,positive_bool) tuples;known atom,exact bool.
Query exact such tuple. Empty clause is false,empty formula true. Enumerate
assignments by binary integer with first atom least significant. Return model
count,entailed flag,and first countermodel or None. Finite propositional only.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def prove(atoms,clauses,query):
    if type(atoms) is not list or not 1<=len(atoms)<=8:raise ValueError('atoms must be exact list1..8')
    positions={}
    for x in atoms:
        if not _label(x) or x in positions:raise ValueError('atoms must be unique valid names')
        positions[x]=len(positions)
    if type(clauses) is not list or len(clauses)>20:raise ValueError('clauses must be exact list0..20')
    def literal(x):
        if type(x) is not tuple or len(x)!=2:raise ValueError('literal must be exact atom polarity tuple')
        a,p=x
        if not _label(a) or a not in positions:raise ValueError('literal atom must be known valid name')
        if type(p) is not bool:raise ValueError('literal polarity must be exact bool')
    for clause in clauses:
        if type(clause) is not list or len(clause)>8:raise ValueError('clause must be exact list0..8')
        for x in clause:literal(x)
    literal(query);models=0;counter=None
    for bits in range(1<<len(atoms)):
        if all(any(bool(bits & (1<<positions[a]))==p for a,p in clause) for clause in clauses):
            models+=1
            if bool(bits & (1<<positions[query[0]]))!=query[1] and counter is None:counter=[(a,bool(bits & (1<<positions[a]))) for a in atoms]
    return {'models':models,'entailed':counter is None,'countermodel':counter,'general_theorem_inferred':False}

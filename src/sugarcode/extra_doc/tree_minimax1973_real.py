"""Row1973 Tree-of-Thought: finite alternating minimax reasoning-branch tree.
Rows exact list1..100 of exact (id,parent,score) tuples,unique nonblank exact
str IDs1..80. First parent None,others prior IDs. Leaf scores exact ints
-1000..1000,branch scores None. Root maximizes,next depth minimizes,alternating.
Equal values select earlier input child. Return root value,principal branch
and each node's minimax value. No generated language reasoning claim.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def evaluate(rows):
    if type(rows) is not list or not 1<=len(rows)<=100:raise ValueError('rows must be exact list1..100')
    ids={};children=[];depth=[]
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row)!=3:raise ValueError('node must be exact id parent score tuple')
        n,p,score=row
        if not _label(n) or n in ids:raise ValueError('IDs must be unique valid labels')
        if i==0:
            if p is not None:raise ValueError('root parent must be None')
            depth.append(0)
        else:
            if not _label(p) or p not in ids:raise ValueError('parent must be prior valid ID')
            parent=ids[p];children[parent].append(i);depth.append(depth[parent]+1)
        if score is not None and (type(score) is not int or not -1000<=score<=1000):raise ValueError('score must be None or exact int-1000..1000')
        ids[n]=i;children.append([])
    for i,(_,_,score) in enumerate(rows):
        if (children[i] and score is not None) or (not children[i] and score is None):raise ValueError('branch score must be None and leaf score integer')
    values=[None]*len(rows);choices={}
    for i in range(len(rows)-1,-1,-1):
        if not children[i]:values[i]=rows[i][2]
        else:
            pick=(max if depth[i]%2==0 else min)(children[i],key=lambda j:values[j]);choices[i]=pick;values[i]=values[pick]
    path=[];i=0
    while True:
        path.append(rows[i][0])
        if i not in choices:break
        i=choices[i]
    return {'value':values[0],'principal_branch':path,'node_values':[(row[0],values[i]) for i,row in enumerate(rows)],'language_reasoning_inferred':False}

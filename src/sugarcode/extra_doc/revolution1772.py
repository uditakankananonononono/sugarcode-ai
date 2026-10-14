"""Doc row1772 Revolution: PARTIAL supplied categorical timeline changes.

Observations exact list2..100 tuples(time,label), unique exact int times0..1000,
label exact nonblank str1..80. Sort time, report adjacent changes and lengths of
constant-label observation runs. No actual revolution, unrest or political inference.
"""


def audit_changes(observations):
    if type(observations) is not list or not 2<=len(observations)<=100:raise ValueError('observations must be an exact list with 2..100 entries')
    times=set()
    for row in observations:
        if type(row) is not tuple or len(row)!=2:raise ValueError('observation must be a time label tuple')
        t,label=row
        if type(t) is not int or not 0<=t<=1000 or t in times:raise ValueError('times must be unique exact integers in 0..1000')
        times.add(t)
        if type(label) is not str or not 1<=len(label)<=80 or not label.strip():raise ValueError('labels must be nonblank exact strings of 1..80 characters')
    ordered=sorted(observations);changes=[(t,a,u,b) for (t,a),(u,b) in zip(ordered,ordered[1:]) if a!=b]
    runs=[];start=ordered[0][0];label=ordered[0][1];count=0;end=start
    for t,state in ordered:
        if state!=label:runs.append((label,start,end,count));start=t;label=state;count=0
        count+=1;end=t
    runs.append((label,start,end,count))
    return {'changes':changes,'runs':runs,'claim':'PARTIAL','revolution_inferred':False}

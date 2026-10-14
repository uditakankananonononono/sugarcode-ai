"""Row630 Distributed Tracing: supplied single-root span nesting analysis.
Spans (parent,start,end) use parent -1 for root. Integer time intervals, children
must fit parent and sibling overlap is allowed. Self time subtracts UNION of
direct child intervals, not sum. Caps32spans/time0..65536. NOT_CLAIMED: actual
request tracking, instrumentation, network tracing or inferred causation.
"""


def analyze_trace(spans):
    if type(spans) not in (list,tuple):raise TypeError('spans must be a list or tuple')
    n=len(spans)
    if not 1<=n<=32:raise ValueError('span count must be between 1 and 32')
    if any(type(s) not in (list,tuple) or len(s)!=3 for s in spans):raise ValueError('spans must contain parent start end')
    if any(type(v) is not int for s in spans for v in s):raise ValueError('span values must be nonbool integers')
    if any(not -1<=p<n or p==i or not 0<=a<=b<=65536 for i,(p,a,b) in enumerate(spans)):raise ValueError('span indices and times must be valid')
    roots=[i for i,(p,a,b) in enumerate(spans) if p==-1]
    if len(roots)!=1:raise ValueError('trace must have exactly one root')
    depths=[]
    for i,(p,a,b) in enumerate(spans):
        seen={i};j=p;depth=0
        while j!=-1:
            if j in seen:raise ValueError('span parents must be acyclic')
            seen.add(j);depth+=1;j=spans[j][0]
        depths.append(depth)
        if p!=-1 and not spans[p][1]<=a<=b<=spans[p][2]:raise ValueError('child interval must fit parent')
    self_times=[]
    for i,(p,a,b) in enumerate(spans):
        intervals=sorted((x,y) for parent,x,y in spans if parent==i);covered=0;right=a
        for x,y in intervals:
            covered+=max(0,y-max(right,x));right=max(right,y)
        self_times.append(b-a-covered)
    return {'root':roots[0],'depths':depths,'self_times':self_times,'request_observed':False}

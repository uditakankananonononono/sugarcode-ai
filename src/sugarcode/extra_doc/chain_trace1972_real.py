"""Row1972 Chain-of-Thought: exact executable arithmetic dependency-chain trace.
Initial exact list1..20 (name,value) tuples,unique nonblank exact str names1..80,
values exact ints-1000..1000. Steps exact list0..20 (name,op,left,right) tuples,
new unique names,op exact 'add','subtract','multiply',operands previously defined
names. Each step records operands/result;results bounded by no extra numeric cap.
Return final environment and trace in definition order. No natural-language
reasoning generation or reasoning correctness outside this arithmetic model.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def execute(initial,steps):
    if type(initial) is not list or not 1<=len(initial)<=20:raise ValueError('initial must be exact list1..20')
    values={}
    for row in initial:
        if type(row) is not tuple or len(row)!=2:raise ValueError('initial row must be exact name value tuple')
        n,v=row
        if not _label(n) or n in values:raise ValueError('names must be unique valid labels')
        if type(v) is not int or not -1000<=v<=1000:raise ValueError('initial value must be exact int-1000..1000')
        values[n]=v
    if type(steps) is not list or len(steps)>20:raise ValueError('steps must be exact list0..20')
    trace=[]
    for row in steps:
        if type(row) is not tuple or len(row)!=4:raise ValueError('step must be exact name operation left right tuple')
        n,op,left,right=row
        if not _label(n) or n in values:raise ValueError('names must be unique valid labels')
        if type(op) is not str or op not in ('add','subtract','multiply'):raise ValueError('operation must be exact add subtract multiply string')
        if not _label(left) or left not in values:raise ValueError('left must be previously defined valid name')
        if not _label(right) or right not in values:raise ValueError('right must be previously defined valid name')
        a,b=values[left],values[right];result=a+b if op=='add' else a-b if op=='subtract' else a*b
        values[n]=result;trace.append((n,op,a,b,result))
    return {'environment':list(values.items()),'trace':trace,'language_reasoning_inferred':False}

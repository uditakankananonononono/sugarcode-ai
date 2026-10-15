"""Row1842 Counterfactual History.
PARTIAL: supplied acyclic binary circuit single-node intervention arithmetic.
evaluate(nodes): exact list1..6 of exact tuple3(op,a,b). op exact int0..4:
0 constant0,1 constant1 (a=b=0 required);2 AND,3 OR,4 XOR with a,b exact integer
indices strictly before this node. Validate outer,each tuple,op,a,b,then
constant fields or predecessor bounds. Return baseline all-node bits and
for each node [forced0target,forced1target], target final node. Intervened
node ignores its equation; all others unchanged. No historical validity.
"""
SCOPE='PARTIAL: supplied acyclic binary circuit single-node intervention arithmetic'
NOT_CLAIMED=('historical causality','counterfactual validity','real history','production readiness')


def evaluate(nodes):
    if type(nodes) is not list or not 1<=len(nodes)<=6:raise ValueError('nodes exact list1..6')
    for i,row in enumerate(nodes):
        if type(row) is not tuple or len(row)!=3:raise ValueError('node exact tuple3')
        op,a,b=row
        if type(op) is not int or not 0<=op<=4:raise ValueError('operation exact int0..4')
        if type(a) is not int or type(b) is not int:raise ValueError('arguments exact integers')
        if op<2:
            if a!=0 or b!=0:raise ValueError('constant arguments must0')
        elif not 0<=a<i or not 0<=b<i:raise ValueError('arguments must reference earlier nodes')
    def run(fixed=None,value=0):
        bits=[]
        for i,(op,a,b) in enumerate(nodes):
            if i==fixed:bit=value
            elif op<2:bit=op
            elif op==2:bit=bits[a]&bits[b]
            elif op==3:bit=bits[a]|bits[b]
            else:bit=bits[a]^bits[b]
            bits.append(bit)
        return bits
    return {'baseline':run(),'intervention_targets':[[run(i,0)[-1],run(i,1)[-1]] for i in range(len(nodes))],'history_validated':False}

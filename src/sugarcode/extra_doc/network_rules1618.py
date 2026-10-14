"""Network Security.

PARTIAL: caller integer-port first-match rule simulation only, not network
security, firewall enforcement, packet inspection or vulnerability assessment.
No network access or changes. Rules/default are caller declarations.
"""
SCOPE='caller integer-port rule simulation only; no firewall enforcement or security claims'


def evaluate(rules,ports,default):
    """Rules exactlist/tuple0..64 rows(lo,hi,action),inclusive exactint ports
    0..65535 with lo<=hi;action/default exactstr 'allow' or 'deny'. Ports exact
    list/tuple1..64 exactint0..65535. Preserve rule and query order;first matching
    rule wins. Return(port,action,zero-based rule index or None for default).
    Overlap allowed. Mixedrowcontainers accepted. No IPs/protocols inferred.
    """
    def action(x):
        if type(x) is not str or x not in ('allow','deny'):raise ValueError('action must be exactstr allow or deny')
    action(default)
    if type(rules) not in (list,tuple) or len(rules)>64:raise ValueError('rules must be exactlist/tuple atmost64')
    parsed=[]
    for row in rules:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('rule must be exactlist/tuple triple')
        lo,hi,decision=row
        if type(lo) is not int or type(hi) is not int or not 0<=lo<=hi<=65535:raise ValueError('rule ports must be exactint0..65535 with lo<=hi')
        action(decision);parsed.append((lo,hi,decision))
    if type(ports) not in (list,tuple) or not 1<=len(ports)<=64:raise ValueError('ports must be exactlist/tuple length1..64')
    for port in ports:
        if type(port) is not int or not 0<=port<=65535:raise ValueError('port must be exactint0..65535')
    result=[]
    for port in ports:
        chosen=default;index=None
        for i,(lo,hi,decision) in enumerate(parsed):
            if lo<=port<=hi:chosen=decision;index=i;break
        result.append((port,chosen,index))
    return {'decisions':tuple(result),'scope':SCOPE}

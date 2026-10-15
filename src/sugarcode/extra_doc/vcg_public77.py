"""Row77 Mechanism Design - Creates rules that incentivize desired behavior.
PARTIAL: finite public-alternative VCG Clarke pivot transfer calculation. Exact
dict values, costs. Values exact list2..5 agent rows, common width2..5, exact
integer reported values0..8. Costs exact alternative-width list ints0..10.
Choose alternative maximizing sum agent values minus cost, ties first index.
Payment_i=max alternative welfare without i - welfare without i at chosen
alternative, always nonnegative. Return alternative, welfare integer, payments,
utilities (reported value minus payment), claims3False. No outside alternative
is silently added; reports need not be truthful. No real mechanism deployed.
NOT_CLAIMED: real incentive guarantee, truthful reports, production readiness.
"""
SCOPE='PARTIAL: exact supplied finite public-alternative Clarke pivot transfers only'
NOT_CLAIMED=('real incentive guarantee','truthful reports','production readiness')


def mechanism(data):
    if type(data) is not dict or set(data)!={'values','costs'}:
        raise ValueError('exact dict with values and costs required')
    values=data['values'];costs=data['costs']
    if type(values) is not list or not 2<=len(values)<=5:
        raise ValueError('values must be an exact list of 2..5 agent rows')
    width=None
    for row in values:
        if type(row) is not list or not 2<=len(row)<=5 or (width is not None and len(row)!=width):
            raise ValueError('value rows must be exact equal-width lists of 2..5 items')
        width=len(row)
        for v in row:
            if type(v) is not int or not 0<=v<=8:
                raise ValueError('values must be exact integers 0..8')
    if type(costs) is not list or len(costs)!=width:
        raise ValueError('costs must be an exact alternative-width list')
    for v in costs:
        if type(v) is not int or not 0<=v<=10:
            raise ValueError('costs must be exact integers 0..10')
    welfare=[sum(row[j] for row in values)-costs[j] for j in range(width)]
    chosen=welfare.index(max(welfare));payments=[]
    for row in values:
        without=[welfare[j]-row[j] for j in range(width)]
        payments.append(max(without)-without[chosen])
    utilities=[row[chosen]-p for row,p in zip(values,payments)]
    return {'alternative':chosen,'welfare':welfare[chosen],'payments':payments,'utilities':utilities,'claims':[False,False,False]}

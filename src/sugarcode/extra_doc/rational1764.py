"""Doc row1764 Rational Choice: PARTIAL supplied payoff-maximization fixture.

Options exact list2..20 (id,benefit,cost) tuples, unique nonblank exact str1..80
IDs; benefit/cost exact int0..1000. Return net utility per option, maximizers in
input order, regret from best net utility. No behavior, rationality or policy claim.
"""


def evaluate(options):
    if type(options) is not list or not 2<=len(options)<=20:raise ValueError('options must be an exact list with 2..20 entries')
    ids=set()
    for row in options:
        if type(row) is not tuple or len(row)!=3:raise ValueError('option must be an id benefit cost tuple')
        n,b,c=row
        if type(n) is not str or not 1<=len(n)<=80 or not n.strip() or n in ids:raise ValueError('option IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(n)
        if type(b) is not int or not 0<=b<=1000:raise ValueError('benefit must be an integer in 0..1000')
        if type(c) is not int or not 0<=c<=1000:raise ValueError('cost must be an integer in 0..1000')
    utilities=[(n,b-c) for n,b,c in options];best=max(u for n,u in utilities)
    return {'utilities':utilities,'maximizers':[n for n,u in utilities if u==best],'regret':[(n,best-u) for n,u in utilities],'claim':'PARTIAL','behavior_validated':False}

"""Row512 API Design: bounded supplied typed endpoint contract routing.

Endpoints(method,path,required_keys) exact-match request method/path; body keys
must contain all required keys, reject unknown endpoint or missing keys.
Caps32endpoints/16keys/64charpath/32charkey;duplicates rejected. Pure contract
checker, no HTTP. NOT_CLAIMED: actual API created/deployed, auth, network,
semantic payload validation, HTTP compliance or real requests executed.
"""


def route_contract(endpoints,method,path,body_keys):
    if type(endpoints) not in (list,tuple) or type(body_keys) not in (list,tuple):raise TypeError('inputs must be lists or tuples')
    if not 1<=len(endpoints)<=32 or len(body_keys)>16:raise ValueError('endpoint count must be 1..32 and at most 16 body keys allowed')
    if any(type(row) not in (list,tuple) or len(row)!=3 for row in endpoints):raise ValueError('endpoints must contain method path required keys triples')
    if any(type(row[2]) not in (list,tuple) or len(row[2])>16 for row in endpoints):raise ValueError('at most 16 required keys per endpoint allowed')
    def check_route(m,p):
        if type(m) is not str or m not in ('GET','POST','PUT','DELETE'):raise ValueError('method must be GET POST PUT or DELETE')
        if type(p) is not str or not 1<=len(p)<=64 or not p.startswith('/'):raise ValueError('path must start with slash and have length 1 through 64')
    check_route(method,path)
    for m,p,keys in endpoints:check_route(m,p)
    if any(type(k) is not str or not 1<=len(k)<=32 for k in body_keys):raise ValueError('body keys must be strings of length 1 through 32')
    for m,p,keys in endpoints:
        if any(type(k) is not str or not 1<=len(k)<=32 for k in keys):raise ValueError('required keys must be strings of length 1 through 32')
        if len(set(keys))!=len(keys):raise ValueError('required keys must be unique')
    routes=[(m,p) for m,p,k in endpoints]
    if len(set(routes))!=len(routes):raise ValueError('endpoint routes must be unique')
    if (method,path) not in routes:return {'endpoint_index':None,'missing_keys':[],'accepted':False,'request_executed':False}
    index=routes.index((method,path));missing=sorted(set(endpoints[index][2])-set(body_keys))
    return {'endpoint_index':index,'missing_keys':missing,'accepted':not missing,'request_executed':False}

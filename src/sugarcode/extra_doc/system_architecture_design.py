"""Row511 System Architecture Design: exact supplied series/parallel reliability.

Groups are parallel redundant components; groups combine in series. Component
availabilities in basis points, independent failure assumption. Return group
availability/product systemavailability. Component index appears only once.
Caps16components/16groups/16indiceseach. NOT_CLAIMED: architecture deployed,
independence true, measured availability, capacity, latency or safety assurance.
"""
from fractions import Fraction


def architecture_reliability(availability,groups):
    if type(availability) not in (list,tuple) or type(groups) not in (list,tuple):raise TypeError('inputs must be lists or tuples')
    if not 1<=len(availability)<=16 or not 1<=len(groups)<=16:raise ValueError('component and group counts must be between 1 and 16')
    if any(type(row) not in (list,tuple) or not 1<=len(row)<=16 for row in groups):raise ValueError('groups must contain 1 through 16 indices')
    if any(type(v) is not int or not 0<=v<=10000 for v in availability):raise ValueError('availability must be nonbool integers zero through 10000')
    if any(type(i) is not int or not 0<=i<len(availability) for row in groups for i in row):raise ValueError('groups must contain nonbool valid component indices')
    flattened=[i for row in groups for i in row]
    if len(set(flattened))!=len(flattened):raise ValueError('component indices must be globally unique')
    results=[];system=Fraction(1)
    for row in groups:
        failure=Fraction(1)
        for i in row:failure*=1-Fraction(availability[i],10000)
        result=1-failure;results.append(result);system*=result
    return {'group_availability':results,'system_availability':system,'architecture_deployed':False}

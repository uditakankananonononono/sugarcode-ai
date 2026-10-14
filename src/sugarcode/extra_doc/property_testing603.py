"""Row603 Property-Based Testing - Tests invariants.

Bounded property checks on supplied integer-list input/output examples of a sort:
nondecreasing order, equal multiplicities, equal length. No target execution,
random generation, shrinking or universal correctness claim.
"""
from collections import Counter


def check_sort_properties(rows):
    """Rows list1..32 tuple(case_id, input_list, output_list). Exact lowercase
    identifier IDs1..24; each list0..16 exact nonbool integers +/-1000.
    Return property failures independently, not one inferred pass/fail bit.
    """
    if type(rows) is not list:
        raise TypeError('exact case list required')
    if not 1<=len(rows)<=32:
        raise ValueError('case count must be 1..32')
    import re
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple case required')
        if len(row)!=3:
            raise ValueError('case arity must be three')
        case, original, output = row
        if type(case) is not str:
            raise TypeError('exact case identifier string required')
        if not 1<=len(case)<=24 or re.fullmatch(r'[a-z][a-z0-9_]*',case) is None:
            raise ValueError('bounded lowercase case identifier required')
        for values in (original,output):
            if type(values) is not list:
                raise TypeError('exact integer list required')
            if len(values)>16:
                raise ValueError('integer list cap must be at most16')
            for value in values:
                if type(value) is not int:
                    raise TypeError('exact nonbool integer required')
                if not -1000<=value<=1000:
                    raise ValueError('integer outside declared range')
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate case')
    results=[]
    for case,original,output in sorted(rows):
        failures=[]
        if len(original)!=len(output):
            failures.append('length')
        if Counter(original)!=Counter(output):
            failures.append('multiplicity')
        if any(output[i]>output[i+1] for i in range(len(output)-1)):
            failures.append('order')
        results.append((case,failures))
    return {'cases':results,'failed_cases':sum(bool(failures) for _,failures in results)}

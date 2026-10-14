"""Row601 Dynamic Analysis - Finds bugs by running.

SCOPED bounded arithmetic instruction interpreter with execution trace and
first runtime fault. Runs only supplied declarative operations, never Python,
imports, callables or external programs. Not general dynamic code analysis.
"""
from fractions import Fraction


def run_checked(initial, instructions):
    """Initial exact int +/-1,000,000; list1..32 tuple(op, operand).
    Ops add/sub/mul/div/assert_eq, exact integer operands +/-1,000,000.
    Exact rational state capped at numerator/denominator magnitude2**256 after
    every operation. Division by zero, failed assertion or state cap are faults.
    Validation of ALL instructions precedes execution. No external effects.
    """
    def integer(value):
        if type(value) is not int:
            raise TypeError('exact nonbool integer required')
        if not -1000000<=value<=1000000:
            raise ValueError('integer outside declared range')
    integer(initial)
    if type(instructions) is not list:
        raise TypeError('exact instruction list required')
    if not 1<=len(instructions)<=32:
        raise ValueError('instruction count must be 1..32')
    for row in instructions:
        if type(row) is not tuple:
            raise TypeError('exact tuple instruction required')
        if len(row)!=2:
            raise ValueError('instruction arity must be two')
        op,operand=row
        if type(op) is not str:
            raise TypeError('exact opcode string required')
        if op not in ('add','sub','mul','div','assert_eq'):
            raise ValueError('unknown opcode')
        integer(operand)
    value=Fraction(initial)
    trace=[]
    fault=None
    for index,(op,operand) in enumerate(instructions):
        before=value
        if op=='div' and operand==0:
            fault=(index,'division_by_zero')
            break
        if op=='assert_eq' and value!=operand:
            fault=(index,'assertion_failed')
            break
        if op=='add':
            value+=operand
        elif op=='sub':
            value-=operand
        elif op=='mul':
            value*=operand
        elif op=='div':
            value/=operand
        if abs(value.numerator)>2**256 or value.denominator>2**256:
            value=before
            fault=(index,'state_cap')
            break
        trace.append((index,op,str(before),str(value)))
    return {'trace':trace,'value_fraction':str(value),'fault':fault,
            'completed':fault is None}

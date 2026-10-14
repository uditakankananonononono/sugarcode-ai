"""Doc row676 Value Object Design: PARTIAL immutable rational value fixture.

make(numerator,denominator) takes exact nonbool ints -1000000..1000000, nonzero
denominator. Return frozen dataclass FractionValue with reduced coprime numerator,
positive denominator; zero normalizes to0/1. Equality/hash by normalized fields.
Direct constructor requires normalized fields and same bounds. No domain model
completeness, money arithmetic or object persistence claimed.
"""
from dataclasses import dataclass
from math import gcd


@dataclass(frozen=True)
class FractionValue:
    numerator: int
    denominator: int

    def __post_init__(self):
        if type(self.numerator) is not int or type(self.denominator) is not int:
            raise ValueError('fields must be exact integers')
        if not -1000000<=self.numerator<=1000000 or not 1<=self.denominator<=1000000:
            raise ValueError('normalized fields exceed bounds')
        if gcd(self.numerator,self.denominator)!=1:
            raise ValueError('fields must be normalized coprime integers')


def make(numerator,denominator):
    if type(numerator) is not int or type(denominator) is not int:
        raise ValueError('inputs must be exact integers')
    if not -1000000<=numerator<=1000000 or not -1000000<=denominator<=1000000 or denominator==0:
        raise ValueError('inputs exceed bounds or denominator is zero')
    divisor=gcd(numerator,denominator)
    sign=-1 if denominator<0 else 1
    return FractionValue(sign*numerator//divisor,abs(denominator)//divisor)

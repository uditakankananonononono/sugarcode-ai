"""Derived-output guard for boundary_response.py:37 dynamic range overflow.

Explicitly import this v2 callable. An unrepresentable finite-input ratio
is refused, rather than returning infinity or silently clipping it.
"""
import math
from .boundary_response import response_curve as _bounded


def response_curve(kd_uM,*,mode='on',hill=1.5,basal=.05,maximum=1,concentrations=None):
    result=_bounded(kd_uM,mode=mode,hill=hill,basal=basal,maximum=maximum,concentrations=concentrations)
    def check(value):
        if isinstance(value,dict):
            for v in value.values():check(v)
        elif isinstance(value,list):
            for v in value:check(v)
        elif isinstance(value,(int,float)) and not isinstance(value,bool) and not math.isfinite(value):
            raise ValueError('UNREPRESENTABLE: derived response output is nonfinite')
    check(result)
    return result

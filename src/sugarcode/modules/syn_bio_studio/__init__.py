"""Synthetic-biology circuit studio: architecture compilation (NOT/AND/toggle/oscillator/sensor) with Hill-kinetics ODE simulation."""
from .core import *
from .core import __dict__ as _d
__all__=[k for k,v in _d.items() if not k.startswith('_') and (callable(v) or k=='PARTS')]

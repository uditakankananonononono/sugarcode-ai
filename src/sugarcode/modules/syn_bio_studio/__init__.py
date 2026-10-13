"""Synthetic-biology circuit studio: architecture compilation (NOT/AND/toggle/oscillator/sensor) with Hill-kinetics ODE simulation."""
from .core import *
from .core import __dict__ as _d
__all__=[k for k,v in _d.items() if not k.startswith('_') and (callable(v) or k=='PARTS')]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import gillespie_expression  # noqa: E402,F401

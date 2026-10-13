"""STR architecture, mosaicism and instability modeling."""
from .core import *
from .core import __dict__ as _d
__all__=[k for k,v in _d.items() if not k.startswith('_') and callable(v)]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import repeat_instability  # noqa: E402,F401

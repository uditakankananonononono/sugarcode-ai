"""Multi-scale non-coding regulatory inference and perturbation design."""
from .core import *
__all__=[name for name in globals() if not name.startswith('_')]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import variant_counterfactual  # noqa: E402,F401

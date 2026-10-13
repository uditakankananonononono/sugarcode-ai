"""Industrial minimal-genome and bioprocess compiler."""
from .core import *
from .core import __all__

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import ale_trajectory  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import compile_synthetic_life  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import stochastic_control  # noqa: E402,F401

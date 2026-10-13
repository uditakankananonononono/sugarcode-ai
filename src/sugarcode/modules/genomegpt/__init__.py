"""Transparent multimodal genomic sequence and 3D-regulation reasoning."""
from .core import *
__all__=[name for name in globals() if not name.startswith('_')]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import masked_sequence_objective  # noqa: E402,F401

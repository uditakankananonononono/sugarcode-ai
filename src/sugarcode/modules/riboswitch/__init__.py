"""Riboswitch: exact RNA folding, sequence optimization, and response curves."""
from .core import (APTAMERS, design_riboswitch, design_sensor, enhancement_features,
 nussinov_fold, optimize_switch, response_curve, validate_rna)
__all__=["APTAMERS","design_riboswitch","design_sensor","enhancement_features","nussinov_fold","optimize_switch","response_curve","validate_rna"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import optimize_switch  # noqa: E402,F401

"""Neuro-inspired biological model training and causal debugging."""
from .core import *
from .core import __dict__ as _d
__all__=[k for k,v in _d.items() if not k.startswith('_') and callable(v)]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import lesion_study  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import neuro_diagnostics  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import pipeline_report  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import predictive_coding_hierarchy  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import rsa  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import sequence_pipeline_demo  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import synthetic_promoter_dataset  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import train  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import train_on_sequences  # noqa: E402,F401

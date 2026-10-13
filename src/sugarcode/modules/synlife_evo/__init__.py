"""SynLife Evo laboratory-grade long-term synthetic-organism evolution."""
from .core import evolve,simulate_evolution_experiment,optimize_stability,simulate_competition
__all__=["evolve","simulate_evolution_experiment","optimize_stability","simulate_competition"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import evolve  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import optimize_stability  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import simulate_competition  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import simulate_evolution_experiment  # noqa: E402,F401

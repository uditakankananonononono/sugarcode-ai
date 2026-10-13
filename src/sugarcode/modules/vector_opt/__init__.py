"""Vector Opt: capsid engineering - receptor docking, NAb escape, transduction."""
from .core import engineer_capsid, directed_evolution
__all__ = ["engineer_capsid", "directed_evolution"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import directed_evolution  # noqa: E402,F401

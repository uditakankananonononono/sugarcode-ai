"""CellPainter 4D: mechanistic temporal morphology and event analysis."""
from .core import (EVENTS, analyze_morphology_4d, detect_morphology_events,
 enhancement_features, segment_nuclei, simulate_morphology, state_from_nuclei_image, simulate_population_4d, validate_morphology_state)
__all__=["EVENTS","analyze_morphology_4d","detect_morphology_events","enhancement_features",
 "segment_nuclei","simulate_morphology","simulate_population_4d","state_from_nuclei_image","validate_morphology_state"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import simulate_population_4d  # noqa: E402,F401

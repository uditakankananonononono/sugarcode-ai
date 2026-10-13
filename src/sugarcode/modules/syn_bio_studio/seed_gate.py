"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core
from ...seed_check import check_seed

def gillespie_expression(duration=100, transcription=2, translation=5, mrna_decay=0.3, protein_decay=0.1, seed=0):
    seed=check_seed(seed)
    return core.gillespie_expression(duration,transcription,translation,mrna_decay,protein_decay,seed)

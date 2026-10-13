"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import training as core
from ...seed_check import check_seed

def random_profile_hmm(length, alphabet='ACGT', *, seed=0, emission_concentration=1.0, transition_concentration=(8.0, 1.0, 1.0)):
    seed=check_seed(seed)
    return core.random_profile_hmm(length,alphabet,seed=seed,emission_concentration=emission_concentration,transition_concentration=transition_concentration)

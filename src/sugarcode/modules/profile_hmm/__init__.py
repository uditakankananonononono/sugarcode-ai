"""Profile HMMs from multiple alignments (Durbin et al. 1998, Chapter 5), with
Baum-Welch training on unaligned sequences."""
from .core import (REFERENCE, ProfileHMM, brute_force, brute_force_expected_counts,
                   brute_force_paths, build_profile_hmm, forward, infer_alphabet, viterbi)
from .training import (baum_welch, expected_counts, log_likelihood, log_prior, maximize,
                       random_profile_hmm)

__all__ = ["REFERENCE", "ProfileHMM", "brute_force", "brute_force_expected_counts",
           "brute_force_paths", "build_profile_hmm", "forward", "infer_alphabet", "viterbi",
           "baum_welch", "expected_counts", "log_likelihood", "log_prior", "maximize",
           "random_profile_hmm"]

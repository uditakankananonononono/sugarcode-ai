"""P05: one literal characterization of bio.pwm.normalized_score (authored from source, NOT RUN).

Direct synthetic API call, one single-column matrix only. Finding only: no
calibrated binding, policy, source-fix, biological, clinical, standard,
caller or CLI claim.
"""
from sugarcode.bio.pwm import normalized_score


def test_normalized_score_unknown_base_is_unclamped_for_one_single_column_matrix():
    lod = [{"A": 1.0, "C": 0.0, "G": 0.0, "T": 0.0}]
    assert normalized_score("N", lod) == -10.0

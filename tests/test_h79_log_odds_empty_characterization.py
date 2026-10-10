"""One empty literal equality, not log-odds validation."""
from sugarcode.bio.pwm import log_odds_matrix


def test_log_odds_empty_literal_equality():
    assert log_odds_matrix([]) == []

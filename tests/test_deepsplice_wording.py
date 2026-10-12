"""deepsplice user-visible provenance string and docstrings do not call the junction data 'real'."""
from sugarcode.modules.deepsplice import core


def test_pwm_source_string_matches_readme_wording():
    assert core.PWM_SOURCE == "RefSeqGene junctions (1,170 GT-AG sites, 29 genes, title-verified)"


def test_docstrings_drop_real():
    d = core.live_splice_assessment.__doc__
    assert "REAL" not in d and "real intronic" not in d
    assert "real intron length" not in core._outcome_context.__doc__ if core._outcome_context.__doc__ else True

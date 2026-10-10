"""H59: one current-source boundary arithmetic pin, not physical accuracy."""

from sugarcode.bio.sequence import tm_wallace


def test_thirteen_adenines_use_short_branch_arithmetic():
    assert tm_wallace('AAAAAAAAAAAAA') == 26.0

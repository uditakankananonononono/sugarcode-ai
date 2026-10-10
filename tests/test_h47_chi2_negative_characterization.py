"""H47: literal negative-statistic diagnostics, not accuracy validation."""

import pytest

from sugarcode.bio.gstats import chi2_sf


@pytest.mark.parametrize("df", [1, 2, 3])
def test_negative_statistic_diagnostic_precedes_df_dispatch(df):
    with pytest.raises(ValueError) as caught:
        chi2_sf(-1.0, df)
    assert type(caught.value) is ValueError
    assert str(caught.value) == "chi-square statistic must be >= 0"

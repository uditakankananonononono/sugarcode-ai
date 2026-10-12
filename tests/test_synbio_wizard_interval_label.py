"""The Monte-Carlo interval is labeled by what the code takes: 5th and 195th of 200 sorted draws."""
from sugarcode.modules.synbio_wizard.core import run_wizard

KEY = "approx_95pct_interval_5th_195th_of_200_draws"


def test_interval_key_text_and_values_unchanged():
    y = run_wizard("vanillin", seed=9)["steps"]["6_yield_simulation"]
    assert KEY in y and "90pct_CI" not in y
    assert y[KEY] == (0.175, 0.614)
    assert y["mean_titer_fraction"] == 0.395 and y["n_monte_carlo"] == 200
    y0 = run_wizard("vanillin", seed=0)["steps"]["6_yield_simulation"]
    assert y0[KEY] == (0.202, 0.623) and y0["mean_titer_fraction"] == 0.396

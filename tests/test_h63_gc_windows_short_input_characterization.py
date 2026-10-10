"""H63: one current-source short-input fallback, not a general window policy."""

from sugarcode.bio.sequence import gc_windows


def test_short_gc_input_retains_one_start_zero_window():
    assert gc_windows('GC', window=4) == [(0, 1.0)]

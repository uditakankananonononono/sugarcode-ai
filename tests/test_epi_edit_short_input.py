"""Short sequences and short guide windows return a result instead of raising."""
import pytest

from sugarcode.modules.epi_edit.core import design_epigenome_edit


@pytest.mark.parametrize("mode", ["CRISPRi", "CRISPRa"])
@pytest.mark.parametrize("span", [(0, 1), (0, 4), (4, 4), (9, 12)])
def test_four_nt_input_does_not_raise(mode, span):
    r = design_epigenome_edit("ACGT", span, mode)
    assert r["guides"] == []
    assert r["non_permanent"] is True


def test_four_nt_guide_window_inside_longer_sequence_does_not_raise():
    seq = "ACGT" * 150
    r = design_epigenome_edit(seq, (54, 55), "CRISPRa")
    assert r["guide_window"] == [0, 4] and r["guides"] == []


from sugarcode.modules.epi_edit.core import epiedit_diagnostics


@pytest.mark.parametrize("n", [4, 50, 199])
def test_diagnostics_short_input_names_the_minimum(n):
    with pytest.raises(ValueError, match="at least 200 nt"):
        epiedit_diagnostics(("ACGT" * 60)[:n])


def test_diagnostics_at_one_window_still_returns():
    d = epiedit_diagnostics("ACGT" * 50)
    assert d["tile_count"] == 1.0 and d["length"] == 200.0


def test_diagnostics_window_constant_is_the_landscape_tile_width():
    from sugarcode.modules.epi_edit.core import CHROMATIN_WINDOW_NT, chromatin_landscape
    t = chromatin_landscape("ACGT" * 50)["track"]
    assert CHROMATIN_WINDOW_NT == 200 and t[0]["end"] - t[0]["start"] == CHROMATIN_WINDOW_NT


def test_diagnostics_200nt_output_equals_pre_fix_output():
    # literal captured from d3be796 (before the length check) for "ACGT"*50
    assert epiedit_diagnostics("ACGT" * 50) == {'length': 200.0, 'tile_count': 1.0, 'accessibility_mean': 0.35, 'accessibility_std': 0.0, 'accessibility_min': 0.35, 'accessibility_max': 0.35, 'gc_mean': 0.5, 'gc_std': 0.0, 'motif_mean': 0.0, 'motif_max': 0.0, 'graph_nodes': 1.0, 'graph_edges': 0.0, 'effector_occupancy': 0.7, 'recruited_fraction': 0.6621621621621621, 'post_accessibility': 0.1358108108108108, 'post_acetylation': 0.20202702702702707, 'post_methylation': 0.7317567567567567, 'relative_expression': 0.18216216216216222, 'mark_fraction.H3K4me3': 0.0, 'mark_fraction.H3K27ac': 0.0, 'mark_fraction.H3K27me3': 1.0, 'mark_fraction.H3K9me3': 0.0, 'mark_fraction.H3K36me3': 1.0}

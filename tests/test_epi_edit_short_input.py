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

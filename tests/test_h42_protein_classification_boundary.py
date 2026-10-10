"""Reporting threshold with synthetic indices, not physical half-life truth."""
import pytest

from sugarcode.bio import proteinprops


@pytest.mark.parametrize('index,label', [(39.99, 'stable'), (40.0, 'stable'),
                                         (40.01, 'unstable')])
def test_summary_strict_instability_threshold_with_synthetic_index(monkeypatch, index, label):
    calls = []
    def synthetic_index(sequence):
        calls.append(sequence)
        return index
    monkeypatch.setattr(proteinprops, 'instability_index', synthetic_index)
    result = proteinprops.protein_summary('AA')
    assert result['instability_index'] == round(index, 2)
    assert result['instability_prediction'] == label
    assert calls == ['AA']

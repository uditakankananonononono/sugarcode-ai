from sugarcode.modules.bioplayground.boundary_diversity import diversity_metrics

def test_simplex_one_and_ten_thousand_boundaries():
    for freq in [[1],[1]+[0]*9999]:
        r=diversity_metrics(freq)
        assert r['heterozygosity']==0 and r['shannon_entropy']==0 and r['effective_alleles']==1

def test_simplex_tolerance_inside_and_outside():
    import pytest
    # Keep each entry<=1 while sums differ by small binary64 amounts.
    r=diversity_metrics([.5,.5+5e-13])
    assert r['effective_alleles']>1
    with pytest.raises(ValueError,match='sum to one within 1e-12'):diversity_metrics([.5,.5+2e-12])

def test_value_cap_exact_and_just_above():
    import pytest
    assert diversity_metrics([1])['effective_alleles']==1
    with pytest.raises(ValueError,match='probability exceeds cap'):diversity_metrics([1+5e-13])

def test_empty_list_owned_refusal_message():
    import pytest
    with pytest.raises(ValueError,match='bounded nonempty probability list required'):diversity_metrics([])

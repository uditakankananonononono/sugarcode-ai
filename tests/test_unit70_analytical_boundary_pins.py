from sugarcode.modules.bioplayground.boundary_diversity import diversity_metrics

def test_simplex_one_and_ten_thousand_boundaries():
    for freq in [[1],[1]+[0]*9999]:
        r=diversity_metrics(freq)
        assert r['heterozygosity']==0 and r['shannon_entropy']==0 and r['effective_alleles']==1

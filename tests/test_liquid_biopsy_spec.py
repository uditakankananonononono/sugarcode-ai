import numpy as np
from sugarcode.modules.liquid_biopsy import (
    analyze_liquid_biopsy, bayesian_haplotype_inference, enhancement_features,
    integrate_multiomics, longitudinal_trajectory, consensus_denoise,
)


def fixture_features():
    rng=np.random.default_rng(2); x=rng.uniform(0,.002,(3,8,4)); x[:,3,0]=.12; x[:,:,1:]=.95
    return x


def test_consensus_denoise_is_deterministic_weight_free_and_concordance_sensitive():
    import inspect
    from sugarcode.modules.liquid_biopsy import core as lb
    assert "default_rng" not in inspect.getsource(lb.consensus_denoise)
    assert not hasattr(lb, "transformer_denoise")
    a=consensus_denoise(fixture_features()); b=consensus_denoise(fixture_features())
    assert a==b and a["trained"] is False and a["neural"] is False
    p=np.asarray(a["evidence_score"]); assert p.shape==(3,8)
    assert np.mean(p[:,3]) > np.mean(p[:,0])
    # concordance: same allele in 1 of 3 fragments scores lower than in 3 of 3
    x=fixture_features(); y=x.copy(); y[1:,3,0]=.0005
    assert consensus_denoise(y)["evidence_score"][0][3] < consensus_denoise(x)["evidence_score"][0][3]


def test_bayesian_haplotype_missing_data_and_posterior():
    r=bayesian_haplotype_inference([[0,0,np.nan],[0,0,1],[1,1,0],[0,0,1]])
    assert abs(sum(x["posterior_mean"] for x in r["haplotypes"])-1)<1e-6
    assert r["haplotypes"][0]["haplotype"]=="001"


def test_multiomics_has_all_modalities_and_probabilities():
    r=integrate_multiomics([.1,.2],[.7],[1.2,.8],[.4])
    assert len(r["latent_signature"])==4 and r["cancer_probability"] is None
    assert r["tissue_probabilities"]=={}


def test_longitudinal_response_and_progression():
    assert longitudinal_trajectory([{"time":0,"burden":.2},{"time":2,"burden":.1}])["trend"]=="decreasing"
    assert longitudinal_trajectory([{"time":0,"burden":.1},{"time":2,"burden":.2}])["trend"]=="increasing"


def test_exactly_sixty_executable_enhancement_features():
    f=enhancement_features([.01,.02,.03,.1], fragment_lengths=[140,166], methylation=[.2,.8], proteins=[1,2], metabolites=[3,4])
    assert len(f)==60 and all(np.isfinite(v) for v in f.values())
    assert len(set(f))==60


def test_end_to_end_report_contains_every_spec_layer():
    r=analyze_liquid_biopsy(fixture_features(), [[0,0],[0,1],[0,np.nan]],
       [{"id":"v1","chrom":"1","position":100}], coverage=[100,150,50],
       fragment_lengths=[140,166,170], methylation=[.2,.8], proteins=[1,2], metabolites=[.4,.5],
       longitudinal=[{"time":0,"burden":.2},{"time":1,"burden":.1}])
    assert r["enhancement_feature_count"]==60
    assert {"denoising","tumor_architecture","multiomics","longitudinal","report"} <= set(r)
    assert r["report"]["disclaimer"]


def test_bad_shapes_rejected():
    import pytest
    with pytest.raises(ValueError): consensus_denoise([1,2,3])
    with pytest.raises(ValueError): bayesian_haplotype_inference([])

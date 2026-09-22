import numpy as np
from sugarcode.modules.liquid_biopsy import (
    analyze_liquid_biopsy, bayesian_haplotype_inference, enhancement_features,
    integrate_multiomics, longitudinal_trajectory, transformer_denoise,
)


def fixture_features():
    rng=np.random.default_rng(2); x=rng.uniform(0,.002,(3,8,4)); x[:,3,0]=.12; x[:,:,1:]=.95
    return x


def test_transformer_is_real_contextual_attention_and_deterministic():
    a=transformer_denoise(fixture_features()); b=transformer_denoise(fixture_features())
    assert a==b and a["architecture"]["heads"]==4
    att=np.asarray(a["attention"]); assert att.shape==(3,8,8)
    assert np.allclose(att.sum(-1),1)
    assert np.mean(np.asarray(a["somatic_probability"])[:,3]) > np.mean(np.asarray(a["somatic_probability"])[:,0])


def test_bayesian_haplotype_missing_data_and_posterior():
    r=bayesian_haplotype_inference([[0,0,np.nan],[0,0,1],[1,1,0],[0,0,1]])
    assert abs(sum(x["posterior_mean"] for x in r["haplotypes"])-1)<1e-6
    assert r["haplotypes"][0]["haplotype"]=="001"


def test_multiomics_has_all_modalities_and_probabilities():
    r=integrate_multiomics([.1,.2],[.7],[1.2,.8],[.4])
    assert len(r["latent_signature"])==4 and 0<=r["cancer_probability"]<=1
    assert set(r["tissue_probabilities"])=={"lung","colorectal","breast","pancreatic"}


def test_longitudinal_response_and_progression():
    assert longitudinal_trajectory([{"time":0,"burden":.2},{"time":2,"burden":.1}])["trend"]=="response"
    assert longitudinal_trajectory([{"time":0,"burden":.1},{"time":2,"burden":.2}])["trend"]=="progression"


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
    with pytest.raises(ValueError): transformer_denoise([1,2,3])
    with pytest.raises(ValueError): bayesian_haplotype_inference([])

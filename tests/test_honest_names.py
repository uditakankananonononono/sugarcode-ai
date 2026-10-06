import pytest
from omega.registry import REGISTRY

RETRACTED = {
    "genomegpt": "GPT",
    "biogpt_lit": "BioGPT",
    "chemgpt_engine": "ChemGPT",
    "alpha_fold_ui": "AlphaFold",
}


@pytest.mark.parametrize("slug,word", RETRACTED.items())
def test_non_model_modules_do_not_wear_model_names(slug, word):
    spec = REGISTRY[slug]
    assert word not in spec.name
    assert spec.summary.startswith("NOT ")
    assert "slug kept for compatibility" in spec.summary

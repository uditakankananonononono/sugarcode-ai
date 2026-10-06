from omega.registry import REGISTRY


def test_rna_decoder_and_bioimage_do_not_imply_learned_models():
    assert "not a trained or deep model" in REGISTRY["rna_decoder"].summary
    assert "no deep learning" in REGISTRY["bioimage_ai"].summary
    assert "computer vision" not in REGISTRY["bioimage_ai"].summary

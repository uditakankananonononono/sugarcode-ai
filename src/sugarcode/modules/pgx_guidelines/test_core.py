from sugarcode.modules.pgx_guidelines import assess, translate_phenotype

def test_cyp2c19_loss_of_function():
    result = translate_phenotype("CYP2C19", "*1/*2")
    assert result["phenotype"] == "Intermediate metabolizer"
    report = assess("CYP2C19", "*1/*2", "clopidogrel", verify_publication=False)
    assert "alternative P2Y12" in report["guidance"]["recommendation"]

def test_cyp2c19_increased_function():
    assert translate_phenotype("CYP2C19", "*1/*17")["phenotype"] == "Rapid metabolizer"
    assert translate_phenotype("CYP2C19", "*17/*17")["phenotype"] == "Ultrarapid metabolizer"

def test_cyp2d6_copy_number_and_codeine():
    assert translate_phenotype("CYP2D6", "*1x2/*1")["phenotype"] == "Ultrarapid metabolizer"
    report = assess("CYP2D6", "*4/*5", "codeine", verify_publication=False)
    assert report["phenotype_translation"]["phenotype"] == "Poor metabolizer"
    assert report["guidance"]["strength"] == "Strong"

def test_unknown_is_missing_not_inferred():
    result = translate_phenotype("CYP2D6", "*1/*999")
    assert result["phenotype"] == "Missing"
    report = assess("CYP2D6", "*1/*999", "codeine", verify_publication=False)
    assert report["guidance"]["strength"] == "Missing"

def test_unsupported_pair_is_missing():
    report = assess("CYP2C19", "*1/*1", "warfarin", verify_publication=False)
    assert report["guidance"]["recommendation"] == "Missing"

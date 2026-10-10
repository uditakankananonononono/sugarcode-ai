"""AUTHORED, NOT RUN. H16: _neo_diagnostics["binding_model_status"] is a WHOLE-SET label that is accurate for the mixed binding paths:
ridge PSSM (trained on IEDB 2013 measured IC50) for 9-mers whose letters are all standard amino acids after uppercasing (so lowercase standard 9-mers are ridge too), hand-set anchor-motif heuristic for other lengths and non-standard 9-mers, not clinically validated.
Base 2ed698b044dd37c11462829f51517062f9bf7c04. Written BEFORE the source edit. No per-path fields, no API change; the pipeline model_status
('no trained deep model and no clinical validation') and the structural-binding method ('no trained docking/deep model') are UNCHANGED."""
from sugarcode.modules.neohunter import neoantigen_pipeline, structural_mhc_binding

REF = "MKTIIALSYIFCLVFADYKDDDDKAAAAAAAAAALQLRLFGKGGGGGGGGGGGG"
EXPECTED = ("mixed: ridge PSSM trained on IEDB 2013 for 9-mers whose letters are all standard amino acids (after uppercasing), "
            "anchor-motif heuristic for other lengths and for non-standard 9-mers; not clinically validated")


def _run():
    v = [{"id": "v1", "type": "snv", "position": 35, "alt": "Y", "expression": 2, "clonal_fraction": .9}]
    return neoantigen_pipeline(REF, v, ["A*02:01", "B*07:02"], max_peptides=4)


def test_binding_model_status_is_the_accurate_whole_set_label():
    assert _run()["diagnostics"]["binding_model_status"] == EXPECTED


def test_label_no_longer_says_untrained_and_names_both_paths():
    s = _run()["diagnostics"]["binding_model_status"]
    assert "untrained" not in s and "ridge PSSM" in s and "9-mers" in s and "non-standard 9-mers" in s and "uppercasing" in s and "anchor-motif heuristic" in s and "not clinically validated" in s


def test_no_per_path_fields_added_to_diagnostics():
    d = _run()["diagnostics"]
    assert [k for k in d if any(w in k.lower() for w in ("pssm", "ridge", "heuristic", "per_path"))] == []
    assert d["research_use_only"] is True and len(d) >= 50


def test_structural_pipeline_wording_is_unchanged():
    r = _run()
    assert r["model_status"] == "deterministic/mechanistic hermetic models; no trained deep model and no clinical validation"
    assert "no trained docking/deep model" in structural_mhc_binding("YLQLRLFGK", "A*02:01")["method"]

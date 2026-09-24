import numpy as np
import pytest
from cellpainter_synth import field, plate
from sugarcode.modules.cellpainter import (CHANNELS, FEATURE_NAMES, cellpainting_report, extract_cell_features,
                                           profile_image, profile_perturbation, profile_wells,
                                           render_profile_heatmap, segment_cells, validate_stack)


def test_unknown_mechanism_raises_instead_of_flat_profile():
    with pytest.raises(ValueError, match="unknown mechanism"):
        profile_perturbation("hdac_inhibitor")


def test_segmentation_finds_every_nucleus_and_grows_cells():
    seg = segment_cells(field())
    assert seg["n_cells"] == 9
    assert (seg["cells"] > 0).sum() > 3 * (seg["nuclei"] > 0).sum()
    assert set(np.unique(seg["nuclei"])) <= set(np.unique(seg["cells"]))


def test_per_cell_features_cover_all_channels_and_features():
    cells = extract_cell_features(field(), segment_cells(field()))
    assert len(cells) == 9 and all(k in cells[0] for k in FEATURE_NAMES) and len(FEATURE_NAMES) == 25


def test_image_features_respond_to_the_stain_that_changed():
    base, dmg, mito = (profile_image(field(c, seed=1))["profile"] for c in ("DMSO", "dna_damage", "mito_toxin"))
    assert dmg["nucleus:intensity"] > base["nucleus:intensity"] * 1.2
    assert dmg["nucleus:granularity"] > base["nucleus:granularity"]
    assert mito["mitochondria:intensity"] < base["mitochondria:intensity"] * 0.7
    assert mito["er:intensity"] == pytest.approx(base["er:intensity"], rel=0.1)


def test_plate_profiles_separate_conditions_and_annotate_mechanisms():
    r = profile_wells(plate())
    c = r["conditions"]
    assert c["DMSO"]["phenotype_strength"] < 0.5
    assert c["dna_damage"]["distinctive_features"][0]["feature"].startswith("nucleus:")
    assert any(f["feature"].startswith("mitochondria:") for f in c["mito_toxin"]["distinctive_features"])
    assert c["dna_damage"]["reference_mechanism_matches"][0]["mechanism"] == "dna_damage"
    assert c["mito_toxin"]["reference_mechanism_matches"][0]["mechanism"] == "mitochondrial_toxin"
    assert c["microtubule_poison"]["reference_mechanism_matches"][0]["mechanism"] == "microtubule_poison"
    assert all(s["condition"] != name for name, v in c.items() for s in v.get("similar_conditions", []))
    assert r["similarity_matrix"]["dna_damage"]["mito_toxin"] < 0.5


def test_heatmap_renders_every_condition_and_feature(tmp_path):
    r = profile_wells(plate())
    out = tmp_path / "heat.svg"
    svg = render_profile_heatmap(r, str(out))
    assert out.read_text() == svg and svg.startswith("<svg") and svg.count("<rect") == 4 * 25


def test_report_matches_are_leave_one_out():
    p = [profile_perturbation(m) for m in ("dna_damage", "mitochondrial_toxin", "kinase_inhibitor")]
    rep = cellpainting_report(p, [[1] * 25, [1.1] * 25])
    for row in rep["mechanism_matches"]:
        assert all(m["mechanism"] != row["query"] for m in row["matches"])


def test_image_validation():
    with pytest.raises(ValueError, match="shape"):
        validate_stack(np.zeros((3, 32, 32)))
    with pytest.raises(ValueError, match="missing channels"):
        validate_stack({"nucleus": np.zeros((32, 32))})
    with pytest.raises(ValueError, match="no control"):
        profile_wells({"a": {"condition": "drug", "image": field()}})
    reordered = field()[::-1]
    assert np.array_equal(validate_stack(reordered, channels=CHANNELS[::-1]), field())

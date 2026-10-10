"""AUTHORED, NOT RUN. H14: bioimage_ai.count_cells default path -> Otsu + seeded watershed (the cellpainter_4d.segment_nuclei algorithm).
Base 387c8f59ddb41f2767013710d567f18b6b28c8fa. Written BEFORE the source edit.
Rulings applied (peer, relayed by Main): threshold_pct is Optional[float]=None on _segment/count_cells/analyze_image; None/omitted = NEW path;
ANY explicit float (0.0, 50, 60, ...) = LEGACY path bit for bit; None is guarded before the bool/isfinite check; native 8-bit input passes unchanged,
float input is min-max normalised to 0-255; the same five output keys; frozen BBBC001 v1 oracle: UNWEIGHTED mean of per-image |pred-gt|/gt <= 0.11
against the two-human mean, all six per-image errors retained and printed on failure, NO per-image gate; Pillow==12.3.0 pinned in the pyproject dev extra.
DELIBERATE INTERNALS TESTING: dispatch is checked with a pass-through spy on core._segment_nuclei_labels (the real function still runs).
Fixtures (hash-pinned byte-identical copies of the frozen oracle): tests/fixtures/h14_bbbc001/{images/*.tif, BBBC001_v1_counts.txt, input-freeze.json}."""
import hashlib
import inspect
import json
import math
import re
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage

import sugarcode.modules.bioimage_ai.core as core
from sugarcode.modules.bioimage_ai import analyze_image, count_cells

FIX = Path(__file__).resolve().parent / "fixtures" / "h14_bbbc001"
KEYS = {"raw_objects", "cell_count", "debris_filtered", "mean_cell_area_px", "coverage_fraction"}


def _synthetic(seed=0, n=6, size=100):
    img = np.zeros((size, size))
    rng = np.random.default_rng(seed)
    yy, xx = np.ogrid[:size, :size]
    for _ in range(n):
        y, x = rng.integers(10, size - 10, 2)
        img[((yy - y) ** 2 + (xx - x) ** 2) < 25] = 1.0
    return img


def _legacy_reference(img, threshold_pct):
    """Verbatim copy of the pre-H14 _segment body (base 387c8f59), used to pin the legacy path bit for bit."""
    img = np.asarray(img, float)
    bg = ndimage.gaussian_filter(img.astype(float), sigma=max(img.shape) / 8)
    corrected = img.astype(float) - bg
    corrected -= corrected.min()
    if corrected.max() > 0:
        corrected /= corrected.max()
    mask = corrected > (threshold_pct / 100.0 * corrected.max())
    mask = ndimage.binary_opening(mask, iterations=1)
    mask = ndimage.binary_fill_holes(mask)
    return ndimage.label(mask)


def _spy_new_path(monkeypatch):
    real = core._segment_nuclei_labels
    seen = []

    def spy(img8, *a, **k):
        seen.append(np.array(img8, copy=True))
        return real(img8, *a, **k)

    monkeypatch.setattr(core, "_segment_nuclei_labels", spy)
    return seen


# ---- signatures, schema, dependency pin ------------------------------------------------------
@pytest.mark.parametrize("fn", [core._segment, core.count_cells, core.analyze_image])
def test_threshold_pct_signature_is_optional_float_none(fn):
    p = inspect.signature(fn).parameters["threshold_pct"]
    assert p.default is None and p.annotation == "Optional[float]"  # string: from __future__ import annotations


def test_schema_generator_represents_optional_float_as_nullable_number():
    from sugarcode.llm.tools import _schema_for
    assert _schema_for("Optional[float]") == {"type": "number", "nullable": True}


def test_unsupported_nested_list_annotation_is_the_reason_for_catalog_absence():
    """image is annotated list[list[float]]; tools._JSON_TYPES has no such entry, so _schema_for returns None and _tool_from drops the tool."""
    from sugarcode.llm.tools import _schema_for
    assert _schema_for("list[list[float]]") is None


def test_catalog_does_not_expose_count_cells_or_analyze_image():
    """UNCONDITIONAL absence pin of the ACTUAL state (deliberate): both tools are absent from catalog() because of the unsupported
    nested-list annotation above. Exposure is a separate future item (an annotation-shape ruling); this test must be revisited then."""
    from sugarcode.llm.tools import catalog
    cat = catalog()
    assert "bioimage_ai__count_cells" not in cat
    assert "bioimage_ai__analyze_image" not in cat


def test_pillow_version_matches_pyproject_dev_pin():
    import PIL
    text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    dev = re.search(r"^dev\s*=\s*\[(.*?)\]", text, re.S | re.M).group(1)
    pins = re.findall(r'"Pillow==([^"]+)"', dev)
    assert pins == ["12.3.0"] and PIL.__version__ == "12.3.0"


# ---- dispatch ---------------------------------------------------------------------------------
@pytest.mark.parametrize("kwargs", [{}, {"threshold_pct": None}])
def test_omitted_or_none_uses_new_path(monkeypatch, kwargs):
    seen = _spy_new_path(monkeypatch)
    count_cells(_synthetic().tolist(), **kwargs)
    analyze_image(_synthetic().tolist(), **kwargs)
    assert len(seen) == 2


@pytest.mark.parametrize("value", [0.0, 50, 60, 60.0, 100])
def test_any_explicit_float_uses_legacy_path_bit_for_bit(monkeypatch, value):
    seen = _spy_new_path(monkeypatch)
    img = _synthetic(3)
    out = count_cells(img.tolist(), threshold_pct=value)
    analyze_image(img.tolist(), threshold_pct=value)
    assert seen == []  # the new path was never entered, including for explicit 60
    labels, n = _legacy_reference(img, value)
    assert (core._segment(img, value)[0] == labels).all() and core._segment(img, value)[1] == n
    sizes = np.array(ndimage.sum(np.ones_like(labels), labels, range(1, n + 1))) if n else np.array([])
    real = int((sizes >= 5).sum()) if n else 0
    assert out == {"raw_objects": n, "cell_count": real, "debris_filtered": n - real,
                   "mean_cell_area_px": round(float(sizes[sizes >= 5].mean()), 1) if real else 0.0,
                   "coverage_fraction": round(float((labels > 0).mean()), 4)}


def test_none_is_guarded_before_bool_isfinite_and_bad_explicit_values_still_raise():
    core._segment(np.arange(64.0).reshape(8, 8), None)  # must not raise TypeError from math.isfinite(None)
    for bad in (True, float("nan"), -1.0, 101.0):
        with pytest.raises(ValueError):
            core._segment(np.arange(64.0).reshape(8, 8), bad)


# ---- input range ------------------------------------------------------------------------------
def test_native_8bit_passes_unchanged_and_float_is_minmax_normalised(monkeypatch):
    seen = _spy_new_path(monkeypatch)
    native = (_synthetic(1) * 200 + 20).astype(np.uint8)  # integral values within 0..255
    count_cells(native.tolist())
    assert np.array_equal(seen[-1], native.astype(float))
    f = _synthetic(1) * 0.8 + 0.1  # float image in [0.1, 0.9]
    count_cells(f.tolist())
    got = seen[-1]
    assert got.min() == 0.0 and got.max() == 255.0
    assert np.allclose(got, (f - f.min()) / (f.max() - f.min()) * 255.0, atol=1e-9, rtol=0)


def test_constant_image_counts_zero_and_nonfinite_still_raises():
    out = count_cells(np.full((16, 16), 7.0).tolist())
    assert set(out) == KEYS and out["cell_count"] == 0 and out["raw_objects"] == 0
    bad = np.zeros((16, 16)); bad[0, 0] = np.nan
    with pytest.raises(ValueError):
        count_cells(bad)


# ---- target equivalence and keys -----------------------------------------------------------------
def test_default_count_equals_cellpainter_segment_nuclei_cell_count():
    from sugarcode.modules.cellpainter_4d import segment_nuclei
    img8 = (_synthetic(5, n=9, size=128) * 180 + 30).astype(np.uint8)
    out = count_cells(img8.tolist())
    assert set(out) == KEYS
    assert out["cell_count"] == segment_nuclei(img8)["cell_count"]
    assert out["raw_objects"] - out["debris_filtered"] == out["cell_count"]


# ---- area-boundary / output-filter semantics (synthetic labels, not a benchmark) -----------------
def _crafted(monkeypatch):
    """Objects of exact areas 4, 7, 9, 10, 11, 25 (ids 1..6, 1-pixel-high bars on separate rows of a 32 x 32 frame). core._segment is
    replaced by a stub that returns them, so only the count_cells/analyze_image FILTER and output keys are under test here."""
    labels = np.zeros((32, 32), dtype=np.int32)
    for k, area in enumerate([4, 7, 9, 10, 11, 25], start=1):
        labels[2 * k, :area] = k
    monkeypatch.setattr(core, "_segment", lambda img, threshold_pct=None: (labels.copy(), 6))
    return (np.arange(1024).reshape(32, 32) % 200).astype(float).tolist()  # non-constant, integral, within 0..255


def test_new_path_area_boundary_below_10_is_debris_at_or_above_10_counted(monkeypatch):
    image = _crafted(monkeypatch)
    out = count_cells(image)
    assert out == {"raw_objects": 6, "cell_count": 3, "debris_filtered": 3,
                   "mean_cell_area_px": round((10 + 11 + 25) / 3, 1), "coverage_fraction": round(66 / 1024, 4)}
    a = analyze_image(image)
    assert [(c["id"], c["area_px"]) for c in a["cells"]] == [(4, 10), (5, 11), (6, 25)]
    assert a["cell_count"] == 3 and a["segmentation_qc"]["objects_raw"] == 6 and a["segmentation_qc"]["objects_kept"] == 3


@pytest.mark.parametrize("value", [60, 60.0, 0.0])
def test_legacy_path_keeps_the_5_px_filter(monkeypatch, value):
    image = _crafted(monkeypatch)
    out = count_cells(image, threshold_pct=value)
    assert out["raw_objects"] == 6 and out["cell_count"] == 5 and out["debris_filtered"] == 1
    assert out["mean_cell_area_px"] == round((7 + 9 + 10 + 11 + 25) / 5, 1)
    a = analyze_image(image, threshold_pct=value)
    assert [(c["id"], c["area_px"]) for c in a["cells"]] == [(2, 7), (3, 9), (4, 10), (5, 11), (6, 25)]


# ---- frozen BBBC001 v1 oracle ----------------------------------------------------------------------
def _frozen():
    frozen = json.loads((FIX / "input-freeze.json").read_text())
    for name, want in frozen["artifact_sha256"].items():
        assert hashlib.sha256((FIX / name).read_bytes()).hexdigest() == want, name
    rows = []
    for line in (FIX / "BBBC001_v1_counts.txt").read_text().strip().splitlines()[1:]:
        name, a, b = line.split("\t")
        rows.append((name, (int(a) + int(b)) / 2))
    return rows


def test_bbbc001_default_count_cells_unweighted_mean_error_within_11_percent():
    from PIL import Image
    errors = {}
    for name, gt in _frozen():
        arr = np.array(Image.open(FIX / "images" / name))
        assert arr.dtype == np.uint8 and arr.ndim == 2
        pred = count_cells(arr.tolist())["cell_count"]
        errors[name] = abs(pred - gt) / gt
    assert len(errors) == 6
    mean = math.fsum(errors.values()) / len(errors)  # UNWEIGHTED, no per-image gate
    assert mean <= 0.11, f"mean {mean:.4f}; per-image errors {errors}"

"""BUG 54/55 regression: chain-code perimeter (disk circularity ~0.91, not the
1.27 ring-pixel bias) and reconstruction-based regional maxima (a single
elongated cell must not be Voronoi-split at pixelation plateaus)."""
import math
import numpy as np
from sugarcode.modules.bioimage_ai import analyze_image, corrected_segmentation, morphology_table
from sugarcode.modules.bioimage_ai.core import _chain_perimeter, _regional_maxima


def _disk(r=10, s=64):
    yy, xx = np.mgrid[0:s, 0:s]
    return ((yy - s // 2) ** 2 + (xx - s // 2) ** 2 <= r * r).astype(float)


def test_disk_circularity_near_one_not_inflated():
    disk = _disk()
    assert analyze_image(disk, threshold_pct=50)["cells"][0]["circularity"] < 1.1
    assert 0.85 < analyze_image(disk, threshold_pct=50)["cells"][0]["circularity"] < 1.05


def test_chain_perimeter_exact_on_cardinal_shapes():
    sq = np.zeros((40, 40)); sq[10:30, 10:30] = 1.0
    assert _chain_perimeter(sq.astype(bool)) == 76.0
    yy, xx = np.mgrid[0:61, 0:61]
    diamond = (abs(yy - 30) + abs(xx - 30) <= 14)
    assert abs(_chain_perimeter(diamond) - 56 * math.sqrt(2)) < 0.5


def test_single_elongated_cell_not_split():
    yy, xx = np.mgrid[0:80, 0:80]
    img = 50 + 150 * np.exp(-(((yy - 40) ** 2) / (2 * 2.0 ** 2) + ((xx - 40) ** 2) / (2 * 8.0 ** 2)))
    assert corrected_segmentation(img, pixel_size_um=1.0, min_area_um2=5)["cell_count"] == 1


def test_touching_cells_still_split_and_plateau_bar_single():
    yy, xx = np.mgrid[0:64, 0:64]
    pair = np.zeros((64, 64)) + 50
    for py, px in [(32, 24), (32, 38)]:
        pair += 150 * np.exp(-((yy - py) ** 2 + (xx - px) ** 2) / 18.0)
    assert corrected_segmentation(pair, pixel_size_um=1.0, min_area_um2=5)["cell_count"] == 2
    bar = np.zeros((48, 96)) + 50
    bar[20:28, 10:86] = 220
    assert corrected_segmentation(bar, pixel_size_um=1.0, min_area_um2=5)["cell_count"] == 1


def test_morphology_table_uses_chain_perimeter():
    disk = _disk()
    seg = corrected_segmentation(disk * 200 + 50, pixel_size_um=1.0, min_area_um2=5)
    row = morphology_table(disk * 200 + 50, seg)[0]
    assert row["circularity"] < 1.1 and row["perimeter_um"] > 60

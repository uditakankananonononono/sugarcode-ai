from __future__ import annotations
import numpy as np
from scipy import ndimage


def _segment(img: np.ndarray, threshold_pct: float = 60.0) -> tuple[np.ndarray, int]:
    """Background-normalized threshold segmentation + watershed-free labeling."""
    bg = ndimage.gaussian_filter(img.astype(float), sigma=max(img.shape) / 8)
    corrected = img.astype(float) - bg
    corrected -= corrected.min()
    if corrected.max() > 0:
        corrected /= corrected.max()
    mask = corrected > (threshold_pct / 100.0 * corrected.max())
    mask = ndimage.binary_opening(mask, iterations=1)
    mask = ndimage.binary_fill_holes(mask)
    labels, n = ndimage.label(mask)
    return labels, n


def count_cells(image: list[list[float]], threshold_pct: float = 60.0) -> dict:
    """Count cells in a grayscale microscopy image (2D array)."""
    img = np.asarray(image, dtype=float)
    if img.ndim != 2:
        raise ValueError("expecting a 2D grayscale image")
    labels, n = _segment(img, threshold_pct)
    sizes = ndimage.sum(np.ones_like(labels), labels, range(1, n + 1))
    sizes = np.array(sizes) if n else np.array([])
    # split filter: drop debris (<5 px) 
    real = int((sizes >= 5).sum()) if n else 0
    return {
        "raw_objects": n,
        "cell_count": real,
        "debris_filtered": n - real,
        "mean_cell_area_px": round(float(sizes[sizes >= 5].mean()), 1) if real else 0.0,
        "coverage_fraction": round(float((labels > 0).mean()), 4),
    }


def analyze_image(image: list[list[float]], threshold_pct: float = 60.0) -> dict:
    """Full analysis: count, morphology per cell, culture-health summary."""
    img = np.asarray(image, dtype=float)
    labels, n = _segment(img, threshold_pct)
    cells = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(labels == i)
        if len(ys) < 5:
            continue
        area = len(ys)
        h = ys.max() - ys.min() + 1
        w = xs.max() - xs.min() + 1
        aspect = max(h, w) / max(1, min(h, w))
        perimeter = float(np.sum(ndimage.binary_erosion(labels == i) ^ (labels == i)))
        circularity = round(4 * np.pi * area / max(perimeter ** 2, 1e-9), 3)
        intensity = float(img[ys, xs].mean())
        cells.append({"id": i, "area_px": area, "aspect_ratio": round(aspect, 2),
                      "circularity": circularity, "mean_intensity": round(intensity, 2),
                      "centroid": [float(ys.mean()), float(xs.mean())]})
    health = _culture_health(cells, img)
    return {
        "cell_count": len(cells),
        "cells": cells,
        "culture_health": health,
        "segmentation_qc": {"objects_raw": n, "objects_kept": len(cells),
                            "correction": "size-filter + fill-holes + opening"},
    }


def _culture_health(cells: list[dict], img: np.ndarray) -> dict:
    if not cells:
        return {"confluence_pct": 0.0, "morphology": "no cells detected", "verdict": "empty/failed"}
    area = sum(c["area_px"] for c in cells)
    confluence = round(100 * area / img.size, 1)
    round_cells = sum(1 for c in cells if c["circularity"] > 0.8 and c["area_px"] < 50)
    frac_round = round_cells / len(cells)
    morphology = ("healthy spread" if frac_round < 0.15 else
                  "stress - many rounded cells" if frac_round < 0.4 else
                  "poor - predominantly rounded/detaching")
    return {"confluence_pct": confluence, "rounded_fraction": round(frac_round, 3),
            "morphology": morphology,
            "verdict": "passage soon" if confluence > 80 else "healthy" if frac_round < 0.15 else "check conditions"}

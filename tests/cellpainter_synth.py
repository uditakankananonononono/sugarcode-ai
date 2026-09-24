"""Synthetic 5-channel Cell Painting fields for tests (not product data)."""
import numpy as np


def field(condition="DMSO", seed=0, size=96, n=9):
    rng = np.random.default_rng(seed)
    img = rng.normal(0.05, 0.01, (5, size, size))
    yy, xx = np.mgrid[:size, :size]
    grid = [(16 + 32 * (k // 3), 16 + 32 * (k % 3)) for k in range(n)]
    for cy, cx in grid:
        cy += rng.integers(-3, 4); cx += rng.integers(-3, 4)
        r = np.hypot(yy - cy, xx - cx)
        nuc = r < 5; cyto = (r < 12) & ~nuc
        dna = 1.0; mito = 0.6; actin_inner, actin_outer = 0.5, 0.5
        if condition == "dna_damage":
            dna = 1.4
        if condition == "mito_toxin":
            mito = 0.25
        if condition == "microtubule_poison":
            actin_inner, actin_outer = 0.15, 0.9
        img[0][nuc] += dna
        if condition == "dna_damage":   # damage foci -> granular, textured DNA stain
            for _ in range(6):
                fy, fx = cy + rng.integers(-3, 4), cx + rng.integers(-3, 4)
                img[0][(np.hypot(yy - fy, xx - fx) < 1.2)] += 1.2
        img[1][cyto] += 0.5                                     # ER
        img[2][cyto & (r < 8)] += actin_inner                   # actin/Golgi
        img[2][cyto & (r >= 8)] += actin_outer
        img[3][nuc & (r < 2)] += 0.8                            # nucleoli
        img[4][cyto] += mito                                    # mitochondria
    return img


def plate(conditions=("DMSO", "dna_damage", "mito_toxin", "microtubule_poison"), reps=3):
    return {f"{c}_{k}": {"condition": c, "image": field(c, seed=100 * i + k)}
            for i, c in enumerate(conditions) for k in range(reps)}

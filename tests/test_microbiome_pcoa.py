"""PCoA must use Gower centering of the squared distances (means of D^2, not D)."""
import numpy as np
from sugarcode.modules.microbiome_exp.core import cohort_analysis


def test_pcoa_matches_explicit_gower_centering():
    table = {
        "A": {"x": 100, "y": 50, "z": 10},
        "B": {"x": 20, "y": 200, "z": 5},
        "C": {"x": 5, "y": 30, "z": 300},
        "D": {"x": 60, "y": 60, "z": 60},
    }
    co = cohort_analysis(table)
    b = np.array(co["bray_curtis"]); n = len(b)
    J = np.eye(n) - np.ones((n, n)) / n
    G = -0.5 * J @ (b ** 2) @ J
    w = np.linalg.eigh(G)[0]
    assert abs(w[-1] - co["ordination"]["eigenvalues"][0]) < 1e-9
    assert abs(w[-2] - co["ordination"]["eigenvalues"][1]) < 1e-9

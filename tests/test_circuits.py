from sugarcode.modules.synbio_studio import Circuit, Gate, simulate, logic_verify
from sugarcode.modules.synbio_studio.core import repressilator, toggle_switch, and_gate
from sugarcode.modules.living_computer import compile_logic, noise_analysis


def test_toggle_switch_bistable():
    c = toggle_switch()
    r1 = simulate(c, (0, 200), y0=[2.0, 0.0], n_points=60)
    r2 = simulate(c, (0, 200), y0=[0.0, 2.0], n_points=60)
    assert r1["steady_state"]["A"] > r1["steady_state"]["B"]
    assert r2["steady_state"]["B"] > r2["steady_state"]["A"]


def test_repressilator_oscillates_or_settles():
    r = simulate(repressilator(), (0, 150), y0=[1.0, 0.0, 0.0], n_points=200)
    series = r["series"]["LacI"]
    assert max(series) > min(series)


def test_and_gate_truth_table():
    r = logic_verify(and_gate(), ["AraC", "AHL"], "GFP")
    outs = {tuple(sorted(row["inputs"].items())): row["output"] for row in r["truth_table"]}
    assert outs[(("AHL", "HIGH"), ("AraC", "HIGH"))] == "HIGH"
    assert outs[(("AHL", "LOW"), ("AraC", "LOW"))] == "LOW"


def test_compile_logic_and():
    r = compile_logic("A AND B")
    assert r["logical_fidelity"] >= 0.75
    assert r["parts"]["reporter"] == "GFP"


def test_noise_analysis_runs():
    r = noise_analysis(and_gate(), external={"AraC": 3.0, "AHL": 3.0}, simulations=20)
    assert r["steady_state_noise"]["GFP"]["mean"] > 0

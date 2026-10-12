"""Scope-honesty wording guards for the BioSimVR module and spec."""
import inspect
from pathlib import Path

from sugarcode.modules.biosimvr import core

SPEC = Path(__file__).resolve().parent.parent / "spec" / "biosimvr.md"


def test_labscene_docstring_drops_vr_framing():
    doc = inspect.getdoc(core.LabScene)
    assert "'VR' world model" not in doc
    assert "headless" in doc and "no VR interface" in doc


def test_run_session_docstring_discloses_scripted_fixed_outputs():
    doc = inspect.getdoc(core.run_session)
    assert "observations + conclusions" not in doc
    assert "0.72" in doc and "scripted" in doc.lower()


def test_simulate_protocol_docstring_drops_validated_framing():
    doc = inspect.getdoc(core.simulate_protocol)
    assert "validated" not in doc
    assert "caller-supplied" in doc


def test_spec_has_correction_entry_for_each_open_claim_row():
    text = SPEC.read_text()
    for row_id in ("S5-104.01.C01", "S5-104.01.C02", "S5-104.01.C03",
                   "S5-104.02.C01", "S5-104.02.C02", "S5-104.03.C01",
                   "S5-104.03.C02", "S5-104.03.C03", "S5-104.03.C04"):
        assert row_id in text, row_id

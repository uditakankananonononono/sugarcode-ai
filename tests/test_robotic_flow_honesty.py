from sugarcode.modules.robotic_flow import core as rf


def test_defaults_are_disclosed_uncalibrated():
    assert "uncalibrated" in rf.pipette_plan([{"source": "A1", "dest": "B1", "volume_ul": 50}])["coefficients_status"]
    assert "uncalibrated" in rf.droplet_error(10, 2)["coefficients_status"]
    assert "uncalibrated" in rf.reagent_status(1, 10)["coefficients_status"]


def test_caller_supplied_measurements_change_output():
    t = [{"source": "A1", "dest": "B1", "volume_ul": 100, "liquid": "x"}]
    lc = {"x": {"viscosity_cp": 1, "aspirate_speed_ul_s": 10, "air_gap_ul": 1}}
    a = rf.pipette_plan(t, liquid_classes=lc, evaporation_fraction_per_min=0.0)
    b = rf.pipette_plan(t, liquid_classes=lc, evaporation_fraction_per_min=0.5)
    assert a["steps"][0]["evaporation_correction_ul"] == 0.0 < b["steps"][0]["evaporation_correction_ul"]
    assert a["steps"][0]["estimated_s"] == 23.0
    assert a["coefficients_status"] == "caller-supplied liquid classes"

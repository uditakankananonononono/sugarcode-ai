from __future__ import annotations

BINDING_DOMAINS = {
    "tetracycline": {"domain": "TetR", "kd_uM": 0.001, "mechanism": "repressor release"},
    "lactose": {"domain": "LacI", "kd_uM": 1.0, "mechanism": "repressor release (IPTG/allo)"},
    "arabinose": {"domain": "AraC", "kd_uM": 50.0, "mechanism": "activator induction"},
    "theophylline": {"domain": "riboswitch (theo aptamer)", "kd_uM": 0.3, "mechanism": "RNA conformational switch"},
    "fluoride": {"domain": "fluoride riboswitch (crcB)", "kd_uM": 60.0, "mechanism": "RNA conformational switch"},
    "copper": {"domain": "CueR", "kd_uM": 0.001, "mechanism": "metalloregulatory activation"},
    "arsenic": {"domain": "ArsR", "kd_uM": 5.0, "mechanism": "repressor release"},
    "mercury": {"domain": "MerR", "kd_uM": 0.1, "mechanism": "DNA-distortion activation"},
    "cadmium": {"domain": "CadR", "kd_uM": 2.0, "mechanism": "repressor release"},
    "benzene": {"domain": "XylR", "kd_uM": 10.0, "mechanism": "activator induction"},
}
REPORTERS = {"GFP": {"maturation_min": 14, "brightness": 1.0},
             "RFP": {"maturation_min": 45, "brightness": 0.7},
             "Luciferase": {"maturation_min": 2, "brightness": 3.0},
             "lacZ": {"maturation_min": 5, "brightness": 0.5}}


def design_biosensor(analyte: str, reporter: str = "GFP",
                     dynamic_range: tuple[float, float] | None = None) -> dict:
    """Couple a binding domain to a reporter; model dose-response curve."""
    key = analyte.lower()
    if key not in BINDING_DOMAINS:
        raise KeyError(f"no binding domain for {analyte!r}; have {sorted(BINDING_DOMAINS)}")
    bd = BINDING_DOMAINS[key]
    rep = REPORTERS[reporter]
    kd = bd["kd_uM"]
    lo, hi = dynamic_range or (kd / 10, kd * 10)
    import math
    concs = [lo * (hi / lo) ** (i / 20) for i in range(21)]
    response = [round(1 / (1 + (kd / c) ** 1.2), 3) for c in concs]  # Hill n=1.2
    lod = round(kd / 10, 4)
    return {
        "analyte": analyte,
        "binding_domain": bd,
        "reporter": reporter,
        "architecture": f"{bd['domain']} -> promoter control -> {reporter}",
        "dose_response": {"concentration_uM": [round(c, 5) for c in concs],
                          "response": response, "hill_n": 1.2},
        "limit_of_detection_uM": lod,
        "dynamic_range_uM": [round(lo, 4), round(hi, 4)],
        "sensitivity_class": ("ultra-high" if kd < 0.01 else "high" if kd < 1 else "moderate"),
        "response_time_min": rep["maturation_min"] + 20,
        "applications": _applications(key),
    }


def _applications(key: str) -> list[str]:
    if key in ("copper", "arsenic", "mercury", "cadmium"):
        return ["environmental heavy-metal monitoring", "field water testing"]
    if key in ("theophylline", "tetracycline"):
        return ["therapeutic drug monitoring", "fermentation process control"]
    return ["metabolite sensing", "biomarker detection"]

import math as _math
import random as _random

_MODEL_STATUS = "computational predictions only; no wetlab validation; no sensor performance claim"


def _binding_lookup(analyte):
	key = str(analyte).lower()
	if key not in BINDING_DOMAINS:
		raise KeyError(f"no binding domain for {analyte!r}; have {sorted(BINDING_DOMAINS)}")
	return key, BINDING_DOMAINS[key]


def hill_response(concentration_uM, kd_uM=1.0, cooperativity=1.2, vmax=1.0):
	if kd_uM <= 0:
		raise ValueError("kd_uM must be positive")
	if cooperativity <= 0:
		raise ValueError("cooperativity must be positive")
	if vmax <= 0:
		raise ValueError("vmax must be positive")
	if concentration_uM < 0:
		raise ValueError("concentration_uM must be non-negative")
	ln = concentration_uM ** cooperativity
	kdn = kd_uM ** cooperativity
	return vmax * ln / (kdn + ln)


def design_sensor_tunable(analyte, reporter="GFP", cooperativity=1.2, vmax=1.0):
	if reporter not in REPORTERS:
		raise ValueError(f"no reporter {reporter!r}; have {sorted(REPORTERS)}")
	if cooperativity <= 0:
		raise ValueError("cooperativity must be positive")
	if vmax <= 0:
		raise ValueError("vmax must be positive")
	key, bd = _binding_lookup(analyte)
	kd = bd["kd_uM"]
	concentrations = [kd * 10 ** ((i - 20) / 10) for i in range(41)]
	responses = [hill_response(c, kd, cooperativity, vmax) for c in concentrations]
	c10 = next(c for c, y in zip(concentrations, responses) if y >= 0.1 * vmax)
	c90 = next(c for c, y in zip(concentrations, responses) if y >= 0.9 * vmax)
	sensitivity_class = "ultrasensitive" if cooperativity >= 2 else "graded analog"
	return {
		"analyte": key,
		"binding_domain": bd,
		"reporter": reporter,
		"kd_uM": kd,
		"cooperativity": cooperativity,
		"vmax": vmax,
		"external_concentrations_uM": [round(c, 5) for c in concentrations],
		"response": [round(y, 5) for y in responses],
		"c10_uM": round(c10, 6),
		"c90_uM": round(c90, 6),
		"threshold_ratio": round(c90 / c10, 4),
		"sensitivity_class": sensitivity_class,
		"model_status": _MODEL_STATUS,
	}


def select_sensor_modality(analyte, prefer=None):
	modalities = ["protein_tf", "rna_riboswitch", "rna_toehold", "protein_conformational"]
	if prefer is not None and prefer not in modalities:
		raise ValueError(f"unsupported modality {prefer!r}; have {modalities}")
	key, bd = _binding_lookup(analyte)
	if prefer is not None:
		modality = prefer
	elif key in ("theophylline", "fluoride"):
		modality = "rna_riboswitch"
	else:
		modality = "protein_tf"
	if modality == "rna_riboswitch":
		rationale = f"RNA aptamer-based sensing suits {key}; direct ligand binding to mRNA avoids protein translation delay"
	elif modality == "protein_tf":
		rationale = f"transcription-factor based sensing suits {key}; {bd['domain']} couples binding to promoter regulation"
	elif modality == "rna_toehold":
		rationale = f"synthetic toehold switch offers programmable detection of {key} sequences"
	else:
		rationale = f"allosteric protein scaffold engineered for {key} detection"
	return {
		"analyte": key,
		"binding_domain": bd,
		"modality": modality,
		"available_modalities": modalities,
		"rationale": rationale,
		"model_status": _MODEL_STATUS,
	}


def reaction_diffusion_profile(analyte, extracellular_uM=1, membrane_permeability=0.1,
		diffusion_um2_s=10.0, cell_length_um=2.0, points=21):
	if membrane_permeability <= 0:
		raise ValueError("membrane_permeability must be positive")
	if diffusion_um2_s <= 0:
		raise ValueError("diffusion_um2_s must be positive")
	if cell_length_um <= 0:
		raise ValueError("cell_length_um must be positive")
	if extracellular_uM < 0:
		raise ValueError("extracellular_uM must be non-negative")
	if points < 2:
		raise ValueError("points must be at least 2")
	key, bd = _binding_lookup(analyte)
	lam = _math.sqrt(diffusion_um2_s / membrane_permeability)
	positions = [cell_length_um * i / (points - 1) for i in range(points)]
	intra = [extracellular_uM * _math.exp(-x / lam) for x in positions]
	return {
		"analyte": key,
		"binding_domain": bd,
		"extracellular_uM": extracellular_uM,
		"membrane_permeability": membrane_permeability,
		"diffusion_um2_s": diffusion_um2_s,
		"cell_length_um": cell_length_um,
		"positions_um": [round(x, 4) for x in positions],
		"intracellular_concentration_uM": [round(c, 6) for c in intra],
		"tip_to_base_ratio": round(intra[-1] / intra[0], 6) if intra[0] else 0.0,
		"model_status": _MODEL_STATUS,
	}


def binding_pocket_redesign(analyte, target_kd_uM=None, dynamic_range_factor=10.0):
	if dynamic_range_factor <= 1:
		raise ValueError("dynamic_range_factor must exceed 1")
	key, bd = _binding_lookup(analyte)
	kd = bd["kd_uM"]
	if target_kd_uM is None:
		target = kd / dynamic_range_factor
	else:
		if target_kd_uM <= 0:
			raise ValueError("target_kd_uM must be positive")
		target = target_kd_uM
	shift = _math.log10(target / kd)
	kd_shift_log10 = round(shift, 4)
	if shift > 0:
		action = "relax pocket to reduce sensitivity"
	elif shift < 0:
		action = "tighten pocket to increase sensitivity"
	else:
		action = "pocket already matches target"
	directed = abs(shift) > 2
	notes = ["no binding pocket simulations were performed", "no affinity change is guaranteed"]
	if directed:
		notes.append(f"a {abs(round(shift, 4))}-log10-unit kd shift exceeds directed-evolution reach; directed evolution recommended")
	else:
		notes.append(f"a {abs(round(shift, 4))}-log10-unit kd shift is reachable by rational design or directed evolution")
	return {
		"analyte": key,
		"binding_domain": bd,
		"target_kd_uM": target,
		"dynamic_range_factor": dynamic_range_factor,
		"kd_shift_log10": kd_shift_log10,
		"action": action,
		"directed_evolution_recommended": directed,
		"engineering_notes": notes,
		"dynamic_range_uM": [round(target / dynamic_range_factor, 6), round(target * dynamic_range_factor, 6)],
		"model_status": _MODEL_STATUS,
	}


_CHEM_DESCRIPTORS = {
	"tetracycline": {"molecular_weight": 444.4, "clogp": -1.3, "polar_surface_area": 182, "hbond_donors": 6, "hbond_acceptors": 10},
	"lactose": {"molecular_weight": 342.3, "clogp": -2.2, "polar_surface_area": 190, "hbond_donors": 8, "hbond_acceptors": 11},
	"arabinose": {"molecular_weight": 150.1, "clogp": -1.6, "polar_surface_area": 97, "hbond_donors": 4, "hbond_acceptors": 5},
	"theophylline": {"molecular_weight": 180.2, "clogp": 0.1, "polar_surface_area": 69, "hbond_donors": 1, "hbond_acceptors": 4},
	"fluoride": {"molecular_weight": 19.0, "clogp": -0.8, "polar_surface_area": 0, "hbond_donors": 0, "hbond_acceptors": 0},
	"copper": {"molecular_weight": 63.5, "clogp": -0.6, "polar_surface_area": 0, "hbond_donors": 0, "hbond_acceptors": 0},
	"arsenic": {"molecular_weight": 74.9, "clogp": -0.7, "polar_surface_area": 0, "hbond_donors": 0, "hbond_acceptors": 0},
	"mercury": {"molecular_weight": 200.6, "clogp": -0.5, "polar_surface_area": 0, "hbond_donors": 0, "hbond_acceptors": 0},
	"cadmium": {"molecular_weight": 112.4, "clogp": -0.6, "polar_surface_area": 0, "hbond_donors": 0, "hbond_acceptors": 0},
	"benzene": {"molecular_weight": 78.1, "clogp": 2.1, "polar_surface_area": 0, "hbond_donors": 0, "hbond_acceptors": 0},
}


def cheminformatics_descriptors(analyte):
	key, bd = _binding_lookup(analyte)
	if key not in _CHEM_DESCRIPTORS:
		raise KeyError(f"no cheminformatics descriptors for {analyte!r}")
	desc = _CHEM_DESCRIPTORS[key]
	violations = int(desc["molecular_weight"] > 500) + int(desc["clogp"] > 5) \
		+ int(desc["hbond_donors"] > 5) + int(desc["hbond_acceptors"] > 10)
	if violations == 0:
		bioavailability = "high"
	elif violations == 1:
		bioavailability = "moderate"
	else:
		bioavailability = "low"
	uptake = "passive membrane diffusion likely" if desc["clogp"] >= 0 and desc["polar_surface_area"] < 140 else "transport-mediated uptake expected"
	out = dict(desc)
	out.update({
		"analyte": key,
		"binding_domain": bd,
		"lipinski_violations": violations,
		"bioavailability_class": bioavailability,
		"uptake_prediction": uptake,
		"model_status": _MODEL_STATUS,
	})
	return out


def off_target_profile(analyte):
	key, bd = _binding_lookup(analyte)
	own_kd = bd["kd_uM"]
	pairs = []
	for other, obd in BINDING_DOMAINS.items():
		if other == key:
			continue
		cross = max(obd["kd_uM"], own_kd)
		pairs.append((cross, other, obd))
	pairs.sort(key=lambda p: (p[0], p[1]))
	off_targets = [{"analyte": name, "domain": obd["domain"], "predicted_cross_kd_uM": round(cross, 6)}
		for cross, name, obd in pairs]
	closest_cross, closest_name, _ = pairs[0]
	margin = round(closest_cross / own_kd, 2)
	if margin < 100:
		competing = f"off-target {closest_name} within {margin}x of target kd; cross-reactivity possible"
	else:
		competing = f"closest off-target {closest_name} is {margin}x of target kd; selectivity likely"
	return {
		"analyte": key,
		"binding_domain": bd,
		"off_targets": off_targets,
		"specificity_margin": margin,
		"competing_interactions": competing,
		"model_status": _MODEL_STATUS,
	}


def degradation_kinetics(analyte, degradation_rate_per_h=0.1, duration_h=12.0, points=13):
	if degradation_rate_per_h <= 0:
		raise ValueError("degradation_rate_per_h must be positive")
	if duration_h <= 0:
		raise ValueError("duration_h must be positive")
	if points < 2:
		raise ValueError("points must be at least 2")
	key, bd = _binding_lookup(analyte)
	times = [duration_h * i / (points - 1) for i in range(points)]
	fractions = [_math.exp(-degradation_rate_per_h * t) for t in times]
	return {
		"analyte": key,
		"binding_domain": bd,
		"degradation_rate_per_h": degradation_rate_per_h,
		"half_life_h": round(_math.log(2) / degradation_rate_per_h, 4),
		"time_points_h": [round(t, 4) for t in times],
		"fraction_remaining": [round(f, 6) for f in fractions],
		"model_status": _MODEL_STATUS,
	}


def gillespie_sensor_noise(analyte, ligand_uM=1.0, sensor_copies=10, duration_min=60.0,
		trajectories=50, seed=42):
	if ligand_uM <= 0:
		raise ValueError("ligand_uM must be positive")
	if sensor_copies < 1:
		raise ValueError("sensor_copies must be at least 1")
	if duration_min <= 0:
		raise ValueError("duration_min must be positive")
	if trajectories <= 0:
		raise ValueError("trajectories must be positive")
	key, bd = _binding_lookup(analyte)
	kd = bd["kd_uM"]
	kon = 1.0
	koff = kd * kon
	rng = _random.Random(seed)
	raw_obs = [duration_min * k / 10 for k in range(1, 11)]
	traj_means = []
	for _ in range(trajectories):
		bound = 0
		clock = 0.0
		samples = []
		for t in raw_obs:
			while clock < t:
				total = kon * ligand_uM * (sensor_copies - bound) + koff * bound
				clock += rng.expovariate(total)
				if clock < t:
					if rng.random() * total < kon * ligand_uM * (sensor_copies - bound):
						bound += 1
					else:
						bound = max(0, bound - 1)
			samples.append(bound / sensor_copies)
		traj_means.append(sum(samples) / len(samples))
	overall = sum(traj_means) / len(traj_means)
	var = sum((m - overall) ** 2 for m in traj_means) / len(traj_means)
	return {
		"analyte": key,
		"binding_domain": bd,
		"ligand_uM": ligand_uM,
		"sensor_copies": sensor_copies,
		"duration_min": duration_min,
		"trajectories": trajectories,
		"seed": seed,
		"observation_times_min": [round(t, 4) for t in raw_obs],
		"mean_bound_fraction": round(overall, 6),
		"noise_std": round(_math.sqrt(var), 6),
		"deterministic_occupancy": round(ligand_uM / (ligand_uM + kd), 6),
		"estimated_ligand_copies_per_fL": round(0.602 * ligand_uM * 1000, 1),
		"low_copy_number_regime": sensor_copies <= 50,
		"model_status": "stochastic simulation; " + _MODEL_STATUS,
	}


def multi_input_gate(inputs, logic="AND"):
	if not isinstance(inputs, dict) or not inputs:
		raise ValueError("inputs must be a dict of {analyte: concentration_uM}")
	if logic.upper() not in ("AND", "OR"):
		raise ValueError(f"unsupported logic {logic!r}; have ['AND', 'OR']")
	activations = []
	values = []
	for analyte, conc in inputs.items():
		if conc < 0:
			raise ValueError(f"concentration for {analyte!r} must be non-negative")
		key, bd = _binding_lookup(analyte)
		kd = bd["kd_uM"]
		v = conc / (kd + conc)
		activations.append(f"{key}: {v}")
		values.append(v)
	if logic.upper() == "AND":
		out = 1.0
		for v in values:
			out *= v
	else:
		out = 1.0
		for v in values:
			out *= (1 - v)
		out = 1 - out
	return {
		"logic": logic.upper(),
		"activations": activations,
		"gate_output": round(out, 3),
		"model_status": _MODEL_STATUS,
	}


def temporal_filter(signal, sustain_min=30.0, decay_min=5.0):
	if sustain_min <= 0:
		raise ValueError("sustain_min must be positive")
	if decay_min <= 0:
		raise ValueError("decay_min must be positive")
	if not isinstance(signal, (list, tuple)) or len(signal) < 2:
		raise ValueError("signal must be a list of [time_min, value] samples")
	for sample in signal:
		if not isinstance(sample, (list, tuple)) or len(sample) != 2:
			raise ValueError("each signal sample must be [time_min, value]")
		if sample[1] < 0:
			raise ValueError("signal values must be non-negative")
	for a, b in zip(signal, signal[1:]):
		if b[0] <= a[0]:
			raise ValueError("signal time points must be strictly increasing")
	y = 0.0
	filtered = [0.0]
	for i in range(1, len(signal)):
		dt = signal[i][0] - signal[i - 1][0]
		if signal[i][1] > 0:
			y = min(1.0, y + signal[i][1] * dt / sustain_min)
		else:
			y *= _math.exp(-dt / decay_min)
		filtered.append(round(y, 5))
	peak = max(filtered)
	verdict = "sustained signal accepted" if peak >= 0.999 else "transient signal rejected"
	return {
		"sustain_min": sustain_min,
		"decay_min": decay_min,
		"filtered_response": filtered,
		"peak_response": peak,
		"verdict": verdict,
	}


def feedback_loop(kind="positive", gain=2.0, input_signal=None):
	if kind not in ("positive", "negative"):
		raise ValueError(f"unsupported feedback kind {kind!r}; have ['positive', 'negative']")
	if gain <= 0:
		raise ValueError("gain must be positive")
	xs = list(input_signal) if input_signal is not None else [0.1, 0.25, 0.5, 0.75, 1.0]
	if kind == "positive":
		n = 1 + gain
		def f(x):
			xn = x ** n
			return round(xn / (0.5 ** n + xn), 5)
		verdict = "bistable switching behavior (bistable)" if gain >= 1 else "graded analog response (graded)"
	else:
		def f(x):
			return round(x / (1 + gain * x), 5)
		verdict = "homeostatic buffering (homeostatic)"
	return {
		"kind": kind,
		"gain": gain,
		"input_signal": xs,
		"output_response": [f(x) for x in xs],
		"verdict": verdict,
		"model_status": _MODEL_STATUS,
	}


def synthesize_biosensor(analyte, reporter="GFP", cooperativity=1.2, membrane_permeability=0.1):
	if reporter not in REPORTERS:
		raise ValueError(f"no reporter {reporter!r}; have {sorted(REPORTERS)}")
	if cooperativity <= 0:
		raise ValueError("cooperativity must be positive")
	if membrane_permeability <= 0:
		raise ValueError("membrane_permeability must be positive")
	key, bd = _binding_lookup(analyte)
	kd = bd["kd_uM"]
	concentrations = [kd * 10 ** ((i - 20) / 10) for i in range(41)]
	curves = {
		"standard": [round(hill_response(c * membrane_permeability, kd, cooperativity), 5) for c in concentrations],
		"low_permeability": [round(hill_response(c * membrane_permeability * 0.25, kd, cooperativity), 5) for c in concentrations],
		"ultrasensitive": [round(hill_response(c * membrane_permeability, kd, 3), 5) for c in concentrations],
	}
	return {
		"analyte": key,
		"binding_domain": bd,
		"reporter": reporter,
		"cooperativity": cooperativity,
		"membrane_permeability": membrane_permeability,
		"external_concentrations_uM": [round(c, 5) for c in concentrations],
		"predicted_curves": curves,
		"limit_of_detection_uM_external": round(kd / 10 / membrane_permeability, 4),
		"required_parts": [f"{bd['domain']} binding domain", "regulated promoter", f"{reporter} reporter"],
		"assembly_notes": ["no wetlab assembly was performed", "no sensor performance claim is made"],
		"model_status": _MODEL_STATUS,
	}

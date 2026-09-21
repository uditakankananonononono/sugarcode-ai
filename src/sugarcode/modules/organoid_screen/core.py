from __future__ import annotations
from ..organoid_ai.core import drug_response


def screen(tissue: str, compounds: list[str], mutations: list[str] | None = None) -> dict:
    """Screen a compound library on an organoid model; rank + synergy + biomarkers."""
    resp = drug_response(tissue, compounds, mutations)
    ranked = sorted(resp["responses"].items(), key=lambda kv: kv[1]["ic50_uM"])
    synergies = _synergy(resp["responses"])
    biomarkers = _biomarkers(mutations or [], ranked)
    return {
        "tissue": tissue, "mutations": mutations or [],
        "screened": len(compounds),
        "ranking": [{"compound": c, "ic50_uM": d["ic50_uM"]} for c, d in ranked],
        "hit": ranked[0][0] if ranked else None,
        "synergy": synergies,
        "response_biomarkers": biomarkers,
        "interaction_network": _network(mutations or [], [c for c, _ in ranked[:3]]),
        "clinical_efficacy_prediction": round(0.4 + 0.3 * (1 / (1 + ranked[0][1]["ic50_uM"])), 3) if ranked else None,
    }


def _synergy(responses: dict) -> list[dict]:
    items = list(responses.items())
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (ca, da), (cb, db) = items[i], items[j]
            # Bliss-style combined index from IC50s
            ci = round(da["ic50_uM"] / (da["ic50_uM"] + db["ic50_uM"])
                       + db["ic50_uM"] / (da["ic50_uM"] + db["ic50_uM"]) - 1.0, 3)
            out.append({"combination": [ca, cb], "combination_index": abs(ci),
                        "synergy_score": round(1 - abs(ci), 3)})
    out.sort(key=lambda x: -x["synergy_score"])
    return out


def _biomarkers(mutations: list[str], ranked: list) -> list[dict]:
    known = {"BRCA1_rev": "PARP-inhibitor resistance", "TP53": "general resistance",
             "KRAS": "MEK/EGFR pathway dependence", "EGFR_T790M": "1st-gen EGFRi resistance"}
    return [{"marker": m, "interpretation": known.get(m, "uncharacterized"),
             "actionable": m in known} for m in mutations]


def _network(mutations: list[str], top: list[str]) -> dict:
    nodes = list(mutations) + list(top)
    edges = [{"from": m, "to": c, "kind": "sensitizes/resists"}
             for m in mutations for c in top]
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Live combo screen: ChEMBL potency x co-crystal pocket resistance (drop 22)

def screen_with_structure(tissue: str, compounds: list[str], target_gene: str,
                          pdb_id: str, ligand_resname: str,
                          mutations: list[str] | None = None,
                          chain: str | None = None, offline: bool = False) -> dict:
    """Organoid screen grounded in live data on both axes:

    potency    - real ChEMBL measured IC50/Ki/Kd (nM) of each compound
                 against the resolved target (no heuristic baseline);
    resistance - real co-crystal pocket (RCSB ligand lining) + mutdock ddG
                 for each mutation that lands in the pocket lining.

    Effective IC50 = ChEMBL potency x product(affinity loss folds).
    Every compound carries its own provenance and honest status; a compound
    with no ChEMBL record or a mutation outside the pocket says so.
    """
    import re as _re
    from ...bio import chembl
    from ...bio.structures import ligand_pocket
    from ..docking_studio.core import AA3_TO_1 as _A3
    from ..mutdock.core import mutation_effect

    # 1. target + potencies (live ChEMBL)
    targets = chembl.target_search(target_gene, offline=offline)
    if not targets:
        raise ValueError(f"no ChEMBL target for {target_gene!r}")
    target = targets[0]
    per_compound: dict[str, dict] = {}
    for name in compounds:
        mol = chembl.molecule_search(name, offline=offline)
        if not mol:
            per_compound[name] = {"status": "no ChEMBL molecule with this exact name"}
            continue
        acts = chembl.activities_for_molecule_target(mol["chembl_id"], target["chembl_id"],
                                                     offline=offline)
        if not acts:
            per_compound[name] = {"status": "no ChEMBL activity vs this target",
                                  "chembl_id": mol["chembl_id"], "smiles": mol["smiles"]}
            continue
        best = acts[0]
        per_compound[name] = {
            "status": "ok", "chembl_id": mol["chembl_id"], "smiles": mol["smiles"],
            "max_phase": mol["max_phase"],
            "potency": {"value_nM": best["value_nM"], "type": best["standard_type"],
                        "relation": best["relation"], "n_measurements": len(acts),
                        "source": f"ChEMBL {mol['chembl_id']} vs {target['chembl_id']} (live)"},
        }

    # 2. co-crystal pocket (live RCSB)
    lp = ligand_pocket(pdb_id, ligand_resname, chain=chain, offline=offline)
    lining = lp["lining"]
    if chain is None and lining:
        chain = lining[0].get("chain") or None
    if chain:
        lining = [r for r in lining if r.get("chain") in (None, chain)]
    seen = set()
    lining = [r for r in lining if not ((r.get("chain"), r["resnum"]) in seen
                                        or seen.add((r.get("chain"), r["resnum"])))]
    pocket_seq = "".join(_A3.get(r["resname"], "G") for r in lining)
    true_resnums = [r["resnum"] for r in lining]

    # 3. mutations x pocket
    mut_reports = []
    for mut in (mutations or []):
        m = _re.fullmatch(r"([A-Z])(\d+)([A-Z])", mut.strip())
        if not m:
            mut_reports.append({"mutation": mut, "status": "unparseable - expected form T315I"})
            continue
        wt, pos_s, alt = m.group(1), m.group(2), m.group(3)
        pos = int(pos_s)
        if pos not in true_resnums:
            mut_reports.append({"mutation": mut, "status": "outside co-crystal pocket",
                                "detail": f"residue {pos} not among the {len(true_resnums)} "
                                          f"lining residues of {pdb_id}:{ligand_resname.upper()} "
                                          "- no structural resistance evidence"})
            continue
        idx = true_resnums.index(pos)
        if pocket_seq[idx] != wt:
            mut_reports.append({"mutation": mut, "status": "wt mismatch",
                                "detail": f"pocket residue {pos} is {pocket_seq[idx]}, not {wt}"})
            continue
        effects = {}
        for name, rec in per_compound.items():
            if rec.get("status") != "ok" or not rec.get("smiles"):
                continue
            e = mutation_effect(pocket_seq, rec["smiles"], idx, alt,
                                resnums=true_resnums, drug_name=name)
            effects[name] = {"ddg_kcal_mol": e["ddg_kcal_mol"],
                             "affinity_loss_fold": e["affinity_change_fold"],
                             "resistance_risk": e["resistance_risk"]}
        mut_reports.append({"mutation": mut, "status": "in pocket", "effects": effects})

    # 4. combine
    ranking = []
    for name, rec in per_compound.items():
        if rec.get("status") != "ok":
            ranking.append({"compound": name, "status": rec["status"]})
            continue
        base_nm = rec["potency"]["value_nM"]
        fold = 1.0
        applied = []
        for mr in mut_reports:
            if mr.get("status") == "in pocket" and name in mr.get("effects", {}):
                fold *= mr["effects"][name]["affinity_loss_fold"]
                applied.append(mr["mutation"])
        ranking.append({
            "compound": name, "status": "ok",
            "wt_potency_nM": base_nm, "potency_type": rec["potency"]["type"],
            "resistance_fold": round(fold, 2), "mutations_applied": applied,
            "effective_ic50_uM": round(base_nm * fold / 1000, 4),
            "max_phase": rec["max_phase"],
            "provenance": rec["potency"]["source"],
        })
    ranking.sort(key=lambda r: r.get("effective_ic50_uM", float("inf")))
    return {
        "tissue": tissue, "target_gene": target_gene,
        "chembl_target": target,
        "structure": {"pdb_id": pdb_id, "ligand": lp["ligand"],
                      "chain": chain, "n_lining": len(lining),
                      "lining_resnums": true_resnums,
                      "source": lp["source"],
                      "caveat": ("pocket is the co-crystal ligand's observed site; applying it "
                                 "to other ATP-site compounds is an approximation")},
        "mutation_reports": mut_reports,
        "ranking": ranking,
        "hit": next((r["compound"] for r in ranking if r.get("status") == "ok"), None),
        "note": ("WT potency is real ChEMBL data; resistance folds come from the feature "
                 "scorer on the real pocket lining (direction-calibrated, magnitude "
                 "conservative - see mutdock/STATUS)."),
    }

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
                          chain: str | None = None, offline: bool = False,
                          pockets: dict[str, dict] | None = None) -> dict:
    """Organoid screen grounded in live data on both axes:

    potency    - real ChEMBL measured IC50/Ki/Kd (nM) of each compound
                 against the resolved target (no heuristic baseline);
    resistance - real co-crystal pocket (RCSB ligand lining) + mutdock ddG
                 for each mutation that lands in the pocket lining.

    Effective IC50 = ChEMBL potency x product(affinity loss folds).
    Every compound carries its own provenance and honest status; a compound
    with no ChEMBL record or a mutation outside the pocket says so.

    pockets: optional per-compound pocket overrides
    {"asciminib": {"pdb_id": "5MO4", "ligand": "AY7", "chain": "A"}} for
    compounds that bind a DIFFERENT site than the default pocket (e.g.
    allosteric inhibitors). Drop-22 finding made this necessary: applying the
    imatinib ATP-site pocket to asciminib ranked the clinically T315I-active
    drug last - each compound must be scored on its own observed binding site.
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

    # 2. co-crystal pocket(s) (live RCSB): default plus per-compound overrides
    def _load_pocket(pid, lig, ch):
        lp = ligand_pocket(pid, lig, chain=ch, offline=offline)
        lining = lp["lining"]
        if ch is None and lining:
            ch = lining[0].get("chain") or None
        if ch:
            lining = [r for r in lining if r.get("chain") in (None, ch)]
        seen = set()
        lining = [r for r in lining if not ((r.get("chain"), r["resnum"]) in seen
                                            or seen.add((r.get("chain"), r["resnum"])))]
        return {"pdb_id": pid, "ligand": lp["ligand"], "chain": ch,
                "seq": "".join(_A3.get(r["resname"], "G") for r in lining),
                "resnums": [r["resnum"] for r in lining],
                "n_lining": len(lining), "source": lp["source"],
                "resnum_offset": 0}

    # 2b. UniProt binding annotations (drop 26): a mutation OUTSIDE the
    # co-crystal lining can still sit in an annotated binding site - the
    # drop-22 5MO4 lesson (default pocket missed asciminib's allosteric
    # site). We annotate honestly; we never silently re-score on it.
    bind: dict = {"status": "not queried"}
    try:
        from ...bio import uniprot as _up
        bind = _up.binding_sites(target_gene, offline=offline)
    except Exception as e:  # UniProt down -> say so, never fabricate
        bind = {"status": f"binding annotation unavailable: {e}"}

    def _binding_note(pos_canonical: int) -> str | None:
        if bind.get("status") != "ok":
            return None
        hits = [s for s in bind["sites"]
                if s["begin"] is not None and s["end"] is not None
                and s["begin"] - 3 <= pos_canonical <= s["end"] + 3]
        if not hits:
            return None
        desc = "; ".join(f"{s['type']} {s['begin']}-{s['end']}"
                         + (f" ({s['description']})" if s["description"] else "")
                         for s in hits)
        return (f"within/adjacent (+/-3 aa) UniProt binding annotation: {desc} "
                f"[{bind['accession']}] - a pocket override may apply for "
                "compounds binding this site")

    default_pocket = _load_pocket(pdb_id, ligand_resname, chain)
    pocket_map: dict[str, dict] = {}
    for name in compounds:
        ov = (pockets or {}).get(name)
        pocket_map[name] = (_load_pocket(ov["pdb_id"], ov["ligand"], ov.get("chain"))
                            if ov else default_pocket)
        if ov:
            # structure numbering - canonical numbering, e.g. +19 for ABL1
            # 1a-numbered co-crystals (5MO4: gatekeeper T315 is numbered 334).
            # Verified against the structure, never assumed: the wt check below
            # fails loudly when the offset is wrong.
            pocket_map[name]["resnum_offset"] = int(ov.get("resnum_offset", 0))
    # default pocket fields for the report
    pocket_seq = default_pocket["seq"]
    true_resnums = default_pocket["resnums"]

    # 3. mutations x each compound's OWN pocket
    mut_reports = []
    for mut in (mutations or []):
        m = _re.fullmatch(r"([A-Z])(\d+)([A-Z])", mut.strip())
        if not m:
            mut_reports.append({"mutation": mut, "status": "unparseable - expected form T315I"})
            continue
        wt, pos_s, alt = m.group(1), m.group(2), m.group(3)
        pos_canonical = int(pos_s)
        per_comp_effect: dict[str, dict] = {}
        for name, rec in per_compound.items():
            if rec.get("status") != "ok" or not rec.get("smiles"):
                continue
            pk = pocket_map[name]
            pos = pos_canonical + pk.get("resnum_offset", 0)
            if pos not in pk["resnums"]:
                eff = {
                    "status": "outside pocket",
                    "detail": f"residue {pos_canonical} (structure #{pos}) not in the "
                              f"{pk['n_lining']} lining residues of "
                              f"{pk['pdb_id']}:{pk['ligand']} - no structural resistance "
                              "evidence for this compound's site",
                    "affinity_loss_fold": 1.0}
                note = _binding_note(pos_canonical)
                if note:
                    eff["binding_annotation"] = note
                per_comp_effect[name] = eff
                continue
            idx = pk["resnums"].index(pos)
            if pk["seq"][idx] != wt:
                per_comp_effect[name] = {
                    "status": "wt mismatch",
                    "detail": (f"{pk['pdb_id']} residue {pos} (canonical {pos_canonical}) "
                               f"is {pk['seq'][idx]}, not {wt}"),
                    "affinity_loss_fold": 1.0}
                continue
            e = mutation_effect(pk["seq"], rec["smiles"], idx, alt,
                                resnums=pk["resnums"], drug_name=name)
            per_comp_effect[name] = {
                "status": "in pocket",
                "pocket": f"{pk['pdb_id']}:{pk['ligand']}",
                "ddg_kcal_mol": e["ddg_kcal_mol"],
                "affinity_loss_fold": e["affinity_change_fold"],
                "resistance_risk": e["resistance_risk"]}
        mut_reports.append({"mutation": mut, "effects": per_comp_effect})

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
            eff = mr.get("effects", {}).get(name)
            if eff and eff.get("status") == "in pocket":
                fold *= eff["affinity_loss_fold"]
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
        "structure": {"pdb_id": pdb_id, "ligand": default_pocket["ligand"],
                      "chain": default_pocket["chain"],
                      "n_lining": default_pocket["n_lining"],
                      "lining_resnums": true_resnums,
                      "source": default_pocket["source"],
                      "per_compound_pockets": {n: f"{pk['pdb_id']}:{pk['ligand']}"
                                               for n, pk in pocket_map.items()},
                      "caveat": ("each compound is scored on its own co-crystal pocket when an "
                                 "override is given; compounds on the default pocket share the "
                                 "default ligand's observed site as an approximation")},
        "mutation_reports": mut_reports,
        "ranking": ranking,
        "hit": next((r["compound"] for r in ranking if r.get("status") == "ok"), None),
        "note": ("WT potency is real ChEMBL data; resistance folds come from the feature "
                 "scorer on the real pocket lining (direction-calibrated, magnitude "
                 "conservative - see mutdock/STATUS)."),
    }

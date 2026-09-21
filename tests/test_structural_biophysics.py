import math
import pytest
from sugarcode.modules.structural_biophysics import (
    StructureInputError, alanine_interface_scan, analyze_interface,
    parse_pdb, shrake_rupley, vina_score)


def atom(serial, name, res, chain, num, x, y, z, element, record="ATOM", alt="", occ=1.0):
    return (f"{record:<6}{serial:5d} {name:^4}{alt:1}{res:>3} {chain:1}{num:4d} "
            f"   {x:8.3f}{y:8.3f}{z:8.3f}{occ:6.2f}{20:6.2f}          {element:>2}")


def complex_pdb():
    rows = [
        atom(1,"N","LYS","A",1,0,0,0,"N"), atom(2,"CA","LYS","A",1,1.4,0,0,"C"),
        atom(3,"CB","LYS","A",1,2.0,1.3,0,"C"), atom(4,"NZ","LYS","A",1,3.2,1.5,0,"N"),
        atom(5,"C","LYS","A",1,1.8,-1.3,0,"C"), atom(6,"O","LYS","A",1,2.9,-1.6,0,"O"),
        atom(7,"N","ASP","B",2,6.5,0,0,"N"), atom(8,"CA","ASP","B",2,5.4,0,0,"C"),
        atom(9,"CB","ASP","B",2,4.8,1.2,0,"C"), atom(10,"OD1","ASP","B",2,4.0,1.6,0,"O"),
        atom(11,"C","ASP","B",2,5.2,-1.4,0,"C"), atom(12,"O","ASP","B",2,4.2,-1.8,0,"O"),
        atom(13,"C1","LIG","L",1,2.0,4.0,0,"C",record="HETATM"),
        atom(14,"O1","LIG","L",1,3.3,4.0,0,"O",record="HETATM"), "END"]
    return "\n".join(rows)+"\n"


def test_parser_preserves_numbering_and_filters_water_hydrogen():
    pdb = complex_pdb() + atom(20,"O","HOH","A",9,0,0,0,"O",record="HETATM") + "\n"
    atoms = parse_pdb(pdb)
    assert len(atoms) == 14
    assert atoms[0].residue_id == "A:LYS1"
    assert {a.chain for a in atoms} == {"A","B","L"}


def test_parser_altloc_chooses_highest_occupancy():
    pdb = "\n".join([atom(1,"CA","ALA","A",1,0,0,0,"C",alt="A",occ=.4),
                       atom(2,"CA","ALA","A",1,9,0,0,"C",alt="B",occ=.6), "END"])
    assert parse_pdb(pdb)[0].xyz[0] == 9


def test_single_atom_sasa_matches_sphere_area():
    a = parse_pdb(atom(1,"C","GLY","A",1,0,0,0,"C")+"\n")
    out = shrake_rupley(a, sphere_points=240)
    expected = 4*math.pi*(1.7+1.4)**2
    assert out["total_A2"] == pytest.approx(expected, rel=.002)


def test_occlusion_reduces_sasa_and_is_deterministic():
    atoms = parse_pdb("\n".join([atom(1,"C","GLY","A",1,0,0,0,"C"), atom(2,"C","GLY","A",2,3,0,0,"C")]))
    one = shrake_rupley(atoms[:1], sphere_points=240)["total_A2"]
    pair1 = shrake_rupley(atoms, sphere_points=240)
    pair2 = shrake_rupley(atoms, sphere_points=240)
    assert pair1 == pair2 and one < pair1["total_A2"] < 2*one


def test_vina_repulsion_and_attraction_respond_to_geometry():
    atoms = parse_pdb(complex_pdb())
    rec, lig = [x for x in atoms if x.chain == "A"], [x for x in atoms if x.chain == "L"]
    normal = vina_score(rec, lig, rotatable_bonds=2)
    clashing = [type(x)(**{**x.__dict__, "xyz": (1.4,0,0)}) for x in lig]
    bad = vina_score(rec, clashing)
    assert normal["raw_terms"]["gauss1"] > 0
    assert bad["raw_terms"]["repulsion"] > normal["raw_terms"]["repulsion"]
    assert normal["raw_terms"]["rotors"] == 2
    assert "Missing" in normal["limitations"][0]


def test_interface_has_buried_area_contacts_and_salt_bridge():
    atoms = parse_pdb(complex_pdb())
    result = analyze_interface(atoms,"A","B",sphere_points=240)
    assert result["buried_surface_area_A2"] > 0
    assert result["atom_contacts"] > 0
    assert ["A:LYS1","B:ASP2"] in result["putative_salt_bridges"]
    assert {x["residue_id"] for x in result["interface_residues"]} == {"A:LYS1","B:ASP2"}


def test_alanine_scan_uses_real_sidechain_contacts():
    scan = alanine_interface_scan(parse_pdb(complex_pdb()),"A","B")
    ids = {x["residue_id"] for x in scan["candidates"]}
    assert {"A:LYS1","B:ASP2"} <= ids
    assert scan["candidates"][0]["cross_interface_contacts"] > 0
    assert "Missing" in scan["limitations"][0]


def test_invalid_inputs_fail_loudly():
    with pytest.raises(StructureInputError): parse_pdb("HEADER only")
    atoms = parse_pdb(complex_pdb())
    with pytest.raises(StructureInputError): analyze_interface(atoms,"A","Z",sphere_points=240)
    with pytest.raises(StructureInputError): shrake_rupley(atoms,sphere_points=5)


def test_atom_contributions_conserve_score():
    from sugarcode.modules.structural_biophysics import vina_atom_contributions
    atoms=parse_pdb(complex_pdb()); rec=[x for x in atoms if x.chain=="A"]; lig=[x for x in atoms if x.chain=="L"]
    total=vina_score(rec,lig,rotatable_bonds=3)["score_kcal_mol"]
    parts=vina_atom_contributions(rec,lig,rotatable_bonds=3)
    assert parts["total_score_kcal_mol"] == pytest.approx(total,abs=2e-4)
    assert parts["strongest_pairs"]
    assert sum(x["contribution_kcal_mol"] for x in parts["receptor_atoms"]) == pytest.approx(parts["pair_score_kcal_mol"]/2,abs=1e-3)


def test_pose_refinement_relieves_clash_deterministically():
    from sugarcode.modules.structural_biophysics import refine_pose, transform_atoms
    atoms=parse_pdb(complex_pdb()); rec=[x for x in atoms if x.chain=="A"]; lig=[x for x in atoms if x.chain=="L"]
    clashing=transform_atoms(lig,translation=(0,-4,0))
    a=refine_pose(rec,clashing,rounds=8,max_displacement_A=5)
    b=refine_pose(rec,clashing,rounds=8,max_displacement_A=5)
    assert a == b
    assert a["refined_score_kcal_mol"] < a["initial_score_kcal_mol"]
    assert a["max_atom_displacement_A"] <= 5
    assert "Missing" in a["limitations"][0]


def test_interface_desolvation_conserves_atomic_contributions():
    from sugarcode.modules.structural_biophysics import interface_desolvation
    atoms=parse_pdb(complex_pdb()); a=[x for x in atoms if x.chain=="A"]; b=[x for x in atoms if x.chain=="B"]
    r=interface_desolvation(a,b,sphere_points=240)
    assert r["total_buried_atomic_sasa_A2"] > 0
    assert sum(x["desolvation_kcal_mol"] for x in r["atom_contributions"]) == pytest.approx(r["desolvation_kcal_mol"],abs=2e-4)
    assert "Missing" in r["limitations"][0]


def test_explicit_torsion_sampling_moves_only_downstream_atoms():
    from sugarcode.modules.structural_biophysics import sample_ligand_torsions
    pdb="\n".join([atom(1,"C","REC","R",1,2,2,0,"C",record="HETATM"),
                    atom(2,"C1","LIG","L",1,0,0,0,"C",record="HETATM"),
                    atom(3,"C2","LIG","L",1,1.5,0,0,"C",record="HETATM"),
                    atom(4,"O3","LIG","L",1,1.5,1.5,0,"O",record="HETATM")])
    atoms=parse_pdb(pdb); rec=[atoms[0]]; lig=atoms[1:]
    r=sample_ligand_torsions(rec,lig,[{"bond":(0,1),"moving_indices":[1,2]}],angles_degrees=[0,90,180],beam_width=3)
    assert r["conformers_evaluated"] == 3
    assert r["best_ligand_xyz"][0] == [0.0,0.0,0.0]
    assert "not guessed" in r["limitations"][0]


def test_torsion_topology_validation():
    from sugarcode.modules.structural_biophysics import sample_ligand_torsions
    atoms=parse_pdb(complex_pdb()); rec=[x for x in atoms if x.chain=="A"]; lig=[x for x in atoms if x.chain=="L"]
    with pytest.raises(StructureInputError):
        sample_ligand_torsions(rec,lig,[{"bond":(0,1),"moving_indices":[0,1]}])

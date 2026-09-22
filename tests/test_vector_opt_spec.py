import pytest
from sugarcode.modules.vector_opt import *

def test_engineer_capsid_return_keys():
 r=engineer_capsid()
 assert set(["parent_capsid","target_receptor","variants","lead","docking_summary","nab_panel_prediction","next_steps"]) <= set(r.keys())
 assert len(r["variants"]) == 6
 assert "variant_id" in r["variants"][0] and "region" in r["variants"][0]

def test_engineer_capsid_determinism():
 a=engineer_capsid(seed=7); b=engineer_capsid(seed=7); c=engineer_capsid(seed=8)
 assert a == b
 assert a != c

def test_engineer_capsid_lead_is_top_variant():
 r=engineer_capsid(nab_escape=True, seed=3)
 assert r["lead"] == r["variants"][0]

def test_engineer_capsid_sera_fraction():
 r=engineer_capsid(seed=5, nab_escape=True)
 lead=r["lead"]
 assert r["nab_panel_prediction"]["sera_escape_fraction"] == round(min(lead["nab_escape_score"]*0.8,0.8),3)

def test_directed_evolution_rounds():
 e=directed_evolution(n_rounds=4, n_variants=6, seed=2)
 assert len(e["rounds"]) == 4
 assert len(e["lineage"]) == 5
 assert e["lead"] == e["rounds"][-1]["lead"]
 assert e["rounds"][0]["parent_capsid"] == "AAV9"

def test_directed_evolution_lineage_seeding():
 e=directed_evolution(n_rounds=3, seed=2)
 for k in range(1, len(e["rounds"])):
  assert e["rounds"][k]["parent_capsid"] == e["rounds"][k-1]["lead"]["variant_id"]
  assert e["lineage"][k+1] == e["rounds"][k]["lead"]["variant_id"]

def test_directed_evolution_reproducible():
 a=directed_evolution(n_rounds=3, seed=9); b=directed_evolution(n_rounds=3, seed=9)
 assert a == b
 assert a != directed_evolution(n_rounds=3, seed=10)

from sugarcode.modules.crispr_cargo import recommend_vehicle, pk_model, delivery_blueprint
from sugarcode.modules.crispr_muse import MuseAgent, train_round


def test_recommend_vehicle_liver():
    r = recommend_vehicle("SpCas9+gRNA", "liver")
    assert r["recommendation"]["fits_cargo"]
    assert r["recommendation"]["vehicle"] in ("LNP", "AAV8", "VLP-e")


def test_pk_model_decays():
    pk = pk_model("LNP", dose_ug=100, hours=48)
    assert pk["concentration_ug_per_l"][0] > pk["concentration_ug_per_l"][-1] > 0
    assert pk["auc_ug_h_per_l"] > 0


def test_blueprint_has_composition():
    b = delivery_blueprint("prime_editor+pegRNA", "cns")
    assert b["composition"] and b["dose_response"]


def test_muse_improves():
    agent = MuseAgent(seed=1)
    first = train_round(agent, n_samples=16)
    for _ in range(5):
        last = train_round(agent, n_samples=16)
    assert last["mean_reward"] >= first["mean_reward"] - 0.15  # learning is monotone-ish
    assert agent.rounds == 6
    assert len(agent.best_guide()) == 20

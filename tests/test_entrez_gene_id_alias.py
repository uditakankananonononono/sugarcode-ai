from sugarcode.bio import entrez as E


def test_gene_id_prefers_official_symbol_over_alias(monkeypatch):
    # real esearch order for HTT[sym] AND human[orgn]: SLC6A4 (alias HTT) first
    monkeypatch.setattr(E, "esearch", lambda db, term, retmax=20, offline=False: ["6532", "3064"])
    monkeypatch.setattr(E, "esummary", lambda db, ids, offline=False:
                        {"6532": {"name": "SLC6A4"}, "3064": {"name": "HTT"}})
    assert E.gene_id("HTT") == "3064"


def test_gene_id_falls_back_to_first(monkeypatch):
    monkeypatch.setattr(E, "esearch", lambda db, term, retmax=20, offline=False: ["1"])
    monkeypatch.setattr(E, "esummary", lambda db, ids, offline=False: {"1": {"name": "X"}})
    assert E.gene_id("Y") == "1"

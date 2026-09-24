from sugarcode.bio import gnomad as G


def _fake(loeuf):
    return lambda q, offline=False: {"data": {"gene": {"symbol": "X", "gnomad_constraint": {
        "pli": 0.99, "lof_z": 4.0, "oe_lof": 0.25, "oe_lof_upper": loeuf, "mis_z": 1.0, "oe_mis": 0.9}}}}


def test_v4_threshold_is_045(monkeypatch):
    # TP53 in gnomAD r4 has LOEUF 0.418: constrained under gnomAD v4 guidance
    monkeypatch.setattr(G, "_post", _fake(0.418))
    c = G.gene_constraint("TP53")
    assert c["lof_constrained"] is True and c["loeuf_threshold"] == 0.45
    monkeypatch.setattr(G, "_post", _fake(0.45))
    assert G.gene_constraint("X")["lof_constrained"] is False


def test_rate_limit_fails_fast(monkeypatch, tmp_path):
    import io, urllib.error, pytest
    calls = []
    def boom(req, timeout=20):
        calls.append(1)
        raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {},
            io.BytesIO(b'{"errors":[{"message":"Query rate limit exceeded. Please try again in a few minutes."}]}'))
    monkeypatch.setattr(G, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(G.urllib.request, "urlopen", boom)
    with pytest.raises(G.GnomADRateLimited):
        G._post("{ gene(gene_symbol: \"ZZZ\") { symbol } }")
    assert len(calls) == 1

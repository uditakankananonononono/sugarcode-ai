"""Module 110 neuro_hub_dashboard against the platform's own health records and registry."""
import pytest
from omega.health import compute_flux
from omega.registry import REGISTRY
from sugarcode.modules.neuro_hub_dashboard import (platform_health, compute_flux_series,
                                                   unified_search, dashboard_snapshot)


def _records(n_down=3):
    recs = compute_flux()["modules"]
    return [dict(r, importable=False) if i < n_down else r for i, r in enumerate(recs)]


def test_degraded_names_from_real_health_records():
    recs = _records()
    h = platform_health(recs)
    assert h["modules_total"] == 95 and h["modules_online"] == 92
    assert h["degraded"] == [r["slug"] for r in recs[:3]]
    assert None not in h["degraded"]


def test_flux_trend_is_order_independent():
    a = {"timestamp": 1, "modules_online": 95, "modules_total": 95}
    b = {"timestamp": 2, "modules_online": 90, "modules_total": 95}
    assert compute_flux_series([b, a])["trend"] == compute_flux_series([a, b])["trend"] < 0
    assert compute_flux_series([b, a])["timestamps"] == [1, 2]


def test_unified_search_whole_tokens_on_registry():
    docs = [{"module": k, "text": v.summary} for k, v in REGISTRY.items()]
    # substring counting matched "a" in all 95 records
    assert len(unified_search("a", docs, 95)["results"]) < 10
    top = unified_search("CRISPR guide RNA design off-target", docs, 1)["results"][0]
    assert top["module"].startswith("crispr")
    with pytest.raises(ValueError):
        unified_search("gene", docs, -1)


def test_snapshot_alert_counts_real_degraded():
    s = dashboard_snapshot(_records(2))
    assert s["alerts"] == ["2 modules degraded"]

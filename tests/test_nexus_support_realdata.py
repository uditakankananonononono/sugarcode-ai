"""Module 112 nexus_support against the platform registry and realistic inquiries."""
from omega.registry import REGISTRY
from sugarcode.modules.nexus_support.core import schedule_queue, classify_inquiry, detect_modules


def test_queue_without_ids_returns_the_optimal_row():
    t = [{"estimated_hours": 1, "priority_score": p} for p in (1, 2, 9)]
    r = schedule_queue(t, 1)
    assert r["selected"] == [t[2]] and r["objective_value"] == 9.0 and len(r["deferred"]) == 2


def test_queue_duplicate_ids_respect_capacity():
    t = [{"ticket_id": "A", "estimated_hours": 1, "priority_score": 1},
         {"ticket_id": "A", "estimated_hours": 1, "priority_score": 9}]
    r = schedule_queue(t, 1)
    assert r["selected"] == [t[1]] and r["used_hours"] == 1.0


def test_keywords_match_whole_words_only():
    for q in ("Please update my billing address", "Can I get rapid results?",
              "How do I rebuild the index?"):
        assert classify_inquiry(q)["primary"] == "question", q
    assert classify_inquiry("The run crashes with a traceback")["primary"] == "bug"
    assert classify_inquiry("We want to integrate via webhooks")["primary"] == "integration"
    assert classify_inquiry("Pipeline failed in production")["urgency_score"] == 3


def test_every_registry_display_name_resolves_without_prefix_collisions():
    extra = {}
    for slug, spec in REGISTRY.items():
        found = [x["module"] for x in detect_modules(f"I have a question about {spec.name}.")]
        assert slug in found, slug
        if len(found) > 1:
            extra[slug] = found
    assert set(extra) == {"synbio_studio", "syn_bio_studio"}  # true name collision
    both = [x["module"] for x in detect_modules("neuro_hub and neuro_hub_dashboard both broke")]
    assert both == ["neuro_hub", "neuro_hub_dashboard"]

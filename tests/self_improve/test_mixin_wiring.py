import pytest

from sugarcode.self_improve.gate import ManualApprovalGate
from sugarcode.self_improve.mixin import SelfImprovingMixin
from sugarcode.self_improve.wiring import attach_all, list_module_slugs


class DummyService(SelfImprovingMixin):
    pass


def test_module_enumeration_is_real():
    slugs = list_module_slugs()
    assert len(slugs) >= 90
    assert "acmg_bayesian" in slugs
    assert len(set(slugs)) == len(slugs)


def test_attach_all_covers_every_module(tmp_path):
    engines = attach_all(state_dir=tmp_path,
                         gate_factory=lambda slug: ManualApprovalGate(tmp_path / f"{slug}.json"))
    assert set(engines) == set(list_module_slugs())


def test_mixin_requires_attachment():
    service = DummyService()
    with pytest.raises(RuntimeError, match="not attached"):
        service.self_improve()


def test_mixin_end_to_end(tmp_path):
    engines = attach_all(state_dir=tmp_path, gate_factory=lambda slug: ManualApprovalGate(
        tmp_path / f"{slug}.json", auto_approve=True))
    service = DummyService()
    engine = engines["acmg_bayesian"]
    service.attach_self_improvement(engine)
    for _ in range(2):
        service.report_capability_gap("filter only pathogenic variants",
                                      exemplar="BRCA1 c.68_69delAG pathogenic")
    report = service.self_improve()
    proposal = report["proposals"][0]
    engine.activate(proposal["key"], approval_id=proposal["approval_id"])
    out = service.dispatch_self_feature(proposal["name"],
                                        ["BRCA1 pathogenic variant", "benign polymorphism"])
    assert out["count"] >= 1
    assert service.self_improvement_status()["features"]

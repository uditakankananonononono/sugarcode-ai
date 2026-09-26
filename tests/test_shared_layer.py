"""SugarCode on the vendored shared layer (instinct_models)."""
import json

import pytest

from instinct_models import Router
from instinct_models.providers import InklingHFRouter, InklingLocal
from sugarcode.llm import shared


def _transport_calling(name, args):
    def t(url, body, headers, timeout):
        assert body["tools"] and all(x["type"] == "function" for x in body["tools"])
        return {"choices": [{"message": {"content": "", "tool_calls": [
            {"function": {"name": name, "arguments": json.dumps(args)}}]}}]}
    return t


def test_config_forces_sugarcode():
    assert shared.shared_config({}).product == "sugarcode"
    with pytest.raises(ValueError):
        shared.shared_config({"INSTINCT_PRODUCT": "atlas"})


def test_shared_tools_are_plain_function_dicts():
    tools, mods = shared.shared_tools("design a CRISPR guide for TP53")
    assert mods and tools and all({"name", "description", "parameters"} <= set(t) for t in tools)


def test_ask_executes_real_tool_via_local_inkling():
    tools, _ = shared.shared_tools("design a CRISPR guide for TP53")
    name = next(t["name"] for t in tools if t["name"].endswith("pam_sites"))
    seq = "ATGCGTACGTTAGCCGGAGGTACGATCGATCGGTAGCTAGCTAGG"
    r = Router([InklingLocal("http://x/v1", "inkling-small", transport=_transport_calling(name, {"seq": seq}))])
    out = shared.shared_ask("design a CRISPR guide for TP53", router=r)
    assert out["ok"] and out["provider"] == "inkling-local"
    assert "error" not in out["tool_results"][0]


def test_private_never_hits_hosted():
    r = Router([InklingHFRouter("thinkingmachines/Inkling-Small", token="hf_x",
                                transport=_transport_calling("x", {}))])
    out = shared.shared_ask("design a CRISPR guide for TP53", router=r, private=True)
    assert not out["ok"] and out["attempts"][0]["outcome"] == "skipped"


def test_unoffered_tool_call_is_refused():
    r = Router([InklingLocal("http://x/v1", "m", transport=_transport_calling("os__system", {"cmd": "ls"}))])
    out = shared.shared_ask("design a CRISPR guide for TP53", router=r)
    assert "not offered" in out["tool_results"][0]["error"]


def test_needle_dataset_through_shared_pipeline(tmp_path):
    m = shared.build_shared_needle_dataset(tmp_path / "n.jsonl", per_tool=2, max_tools=8)
    assert m["product"] == "sugarcode" and m["rows"] > 0 and m["dropped"] == 0
    assert m["off_topic_ratio"] >= 0.1 and not m["warnings"]
    row = json.loads((tmp_path / "n.jsonl").read_text().splitlines()[0])
    assert {"query", "tools", "answers"} <= set(row)


def test_shared_jev_off_without_key():
    jev = shared.shared_jev({})
    assert jev.name == "jev"
    assert not jev.available()


def test_shared_jev_key_resolution():
    assert shared.shared_jev({"INSTINCT_JEV_API_KEY": "sk-s"}).api_key == "sk-s"
    assert shared.shared_jev({"JEV_API_KEY": "sk-j"}).api_key == "sk-j"


def test_shared_jev_evaluate_through_client():
    seen = {}

    def fake(url, body, headers, timeout):
        seen.update(url=url, body=body, headers=headers)
        return {"model": "jev-1.13.0", "answers": {"risk": {"type": "score", "score": 2.3}}, "usage": {}}

    jev = shared.shared_jev({"INSTINCT_JEV_API_KEY": "sk-s"})
    jev.transport = fake
    out = jev.evaluate("sgRNA: GACCT...", {"risk": {"type": "score", "instructions": "Off-target risk",
                                                  "criteria": ["low", "medium", "high"]}})
    assert out["answers"]["risk"]["score"] == 2.3
    assert seen["headers"]["Authorization"] == "Bearer sk-s"
    assert seen["url"] == "https://thejevai.com/v1/systemone"

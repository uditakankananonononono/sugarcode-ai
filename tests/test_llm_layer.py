"""Model layer: profiles, gating, route fallback, tool catalog, trained router, copilot loop.

The copilot test runs a real HTTP server on localhost speaking the OpenAI
chat-completions format, so the client, tool calling and module execution are
exercised end to end without any external network.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from sugarcode.llm import providers as P
from sugarcode.llm.agent import ask
from sugarcode.llm.router import default_router, training_report
from sugarcode.llm.tools import call_tool, catalog, tools_for_modules


def test_builtin_profiles_shape():
    names = set(P.BUILTIN_PROFILES)
    assert {"ollama", "inkling", "inkling-large", "inkling-local", "inkling-vllm", "ornith-local",
            "fugu", "fugu-ultra", "local-transformers", "openai-compatible"} <= names
    assert "union-alpha" not in names
    ink = P.BUILTIN_PROFILES["inkling"]
    assert ink.base_url == "https://router.huggingface.co/v1"
    assert ink.model == "thinkingmachines/Inkling-Small" and ink.api_key_env == "HF_TOKEN"
    assert P.BUILTIN_PROFILES["inkling-vllm"].model == "thinkingmachines/Inkling-Small-NVFP4"
    for p in P.BUILTIN_PROFILES.values():
        assert p.kind in P.KINDS and p.transport in P.TRANSPORTS


def test_inkling_needs_hf_token():
    with pytest.raises(P.ProviderError, match="HF_TOKEN"):
        P.resolve("inkling", env={})
    c = P.resolve("inkling", env={"HF_TOKEN": "hf_x"})
    assert c.api_key == "hf_x" and c.model == "thinkingmachines/Inkling-Small"


def test_paid_requires_key_and_allow_paid():
    with pytest.raises(P.ProviderError, match="SAKANA_API_KEY"):
        P.resolve("fugu", env={})
    with pytest.raises(P.ProviderError, match="paid"):
        P.resolve("fugu", env={"SAKANA_API_KEY": "k"})
    assert P.resolve("fugu-ultra", env={"SAKANA_API_KEY": "k", "SUGARCODE_ALLOW_PAID": "1"}).model == "fugu-ultra"
    assert P.resolve("fugu", env={"SAKANA_API_KEY": "k"}, allow_paid=True).model == "fugu"


def test_default_route_local_then_inkling():
    assert P.parse_route(env={}) == ["ollama", "inkling"]
    assert [c.profile for c in P.resolve_route(env={})[0]] == ["ollama"]
    assert [c.profile for c in P.resolve_route(env={"HF_TOKEN": "t"})[0]] == ["ollama", "inkling"]
    assert P.parse_route(env={"SUGARCODE_MODEL_ROUTE": "inkling-local, ollama"}) == ["inkling-local", "ollama"]
    with pytest.raises(P.ProviderError, match="unknown"):
        P.parse_route(env={"SUGARCODE_MODEL_ROUTE": "ollama,nope"})


def test_custom_profiles_env_json():
    env = {"SUGARCODE_MODEL_PROFILES": json.dumps([{"name": "lab-box", "base_url": "http://10.0.0.5:9000/v1",
                                                     "model": "m", "kind": "self_hosted"}])}
    assert P.resolve("lab-box", env=env).base_url == "http://10.0.0.5:9000/v1"
    bad = {"SUGARCODE_MODEL_PROFILES": json.dumps([{"name": "x", "base_url": "u", "model": "m", "kind": "cloud"}])}
    with pytest.raises(P.ProviderError):
        P.load_profiles(bad)


def test_catalog_exposes_real_module_functions():
    cat = catalog()
    assert len(cat) >= 200 and len({t.module for t in cat.values()}) >= 60
    for t in list(cat.values())[:40]:
        assert t.parameters["type"] == "object" and t.description
        assert set(t.parameters["required"]) <= set(t.parameters["properties"])


def test_call_tool_validates_and_runs():
    t = next(t for t in catalog().values() if t.parameters["required"])
    assert "error" in call_tool(t.name, {})
    assert "error" in call_tool(t.name, {"__bogus__": 1})
    assert "error" in call_tool("no_such__tool", {})
    assert "error" in call_tool(t.name, "{not json")


def test_router_trained_and_beats_chance():
    rep = training_report()
    assert rep["n_modules"] == 88
    assert rep["heldout_passages"]["softmax_top3"] > 5 * rep["heldout_passages"]["majority_top1"]
    r = default_router()
    top = [m["module"] for m in r.route("design guide RNAs for SpCas9 with off-target scoring", k=5)]
    assert set(top) & {"crispr_opt", "crispr_muse", "cfd_offtarget", "mit_offtarget", "crisprater"}
    top = [m["module"] for m in r.route("codon optimize a protein for E. coli expression", k=5)]
    assert "codon_opt" in top


class _FakeOpenAI(BaseHTTPRequestHandler):
    tool_name = None
    tool_args = None
    seen = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        body = json.dumps({"data": [{"id": "test-model"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append(req)
        if any(m["role"] == "tool" for m in req["messages"]):
            tool_msg = [m for m in req["messages"] if m["role"] == "tool"][-1]
            msg = {"role": "assistant", "content": "RESULT " + tool_msg["content"][:200]}
        else:
            msg = {"role": "assistant", "content": "", "tool_calls": [{
                "id": "c1", "type": "function",
                "function": {"name": type(self).tool_name, "arguments": json.dumps(type(self).tool_args)}}]}
        body = json.dumps({"choices": [{"message": msg}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def fake_server():
    srv = HTTPServer(("127.0.0.1", 0), _FakeOpenAI)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{srv.server_port}/v1"
    srv.shutdown()


def test_health_probe(fake_server):
    env = {"SUGARCODE_LLM_BASE_URL": fake_server, "SUGARCODE_LLM_MODEL": "test-model"}
    h = P.resolve("openai-compatible", env=env).health()
    assert h["ok"] and h["model_listed"]
    assert P.resolve("ollama", env={"SUGARCODE_OLLAMA_BASE_URL": "http://127.0.0.1:9/v1"}).health()["ok"] is False


def test_copilot_runs_real_module_tool(fake_server):
    q = "codon optimize a protein for E. coli expression"
    tools = tools_for_modules([m["module"] for m in default_router().route(q, k=3)])
    t = next(t for t in tools if not t.parameters["required"] or
             all(t.parameters["properties"][r].get("type") == "string" for r in t.parameters["required"]))
    _FakeOpenAI.tool_name = t.name
    _FakeOpenAI.tool_args = {r: "MKTAYIAKQRQISFVKSHFSRQ" for r in t.parameters["required"]}
    _FakeOpenAI.seen = []
    env = {"SUGARCODE_LLM_BASE_URL": fake_server, "SUGARCODE_LLM_MODEL": "test-model"}
    res = ask(q, route="openai-compatible", env=env)
    assert res.profile == "openai-compatible" and res.answer.startswith("RESULT")
    assert res.tool_calls and res.tool_calls[0]["tool"] == t.name
    first = _FakeOpenAI.seen[0]
    assert first["tools"] and any(x["function"]["name"] == t.name for x in first["tools"])


def test_copilot_falls_back_and_reports(fake_server):
    env = {"SUGARCODE_OLLAMA_BASE_URL": "http://127.0.0.1:9/v1",
           "SUGARCODE_LLM_BASE_URL": fake_server, "SUGARCODE_LLM_MODEL": "test-model"}
    _FakeOpenAI.tool_name, _FakeOpenAI.tool_args = "no_such__tool", {}
    res = ask("design a synthetic promoter library", route="ollama,openai-compatible", env=env)
    assert res.profile == "openai-compatible"
    assert any("ollama unreachable" in s for s in res.skipped)
    none = ask("design a synthetic promoter library", route="ollama",
               env={"SUGARCODE_OLLAMA_BASE_URL": "http://127.0.0.1:9/v1"})
    assert none.answer is None and none.modules and none.tools and none.error


def test_ailibrary_parsers_offline():
    from sugarcode.llm import ailibrary
    xml = ("<urlset><url><loc>https://www.theailibrary.co/tool/magicshot</loc></url>"
           "<url><loc>https://www.theailibrary.co/blog/x</loc></url>"
           "<url><loc>https://www.theailibrary.co/tool/codeaid</loc></url></urlset>")
    assert ailibrary.parse_sitemap(xml) == ["codeaid", "magicshot"]
    page = ('<title>MagicShot</title><meta property="og:title" content="MagicShot"/>'
            '<meta property="og:description" content="All in one AI image &amp; video generator"/>'
            '<meta property="og:url" content="https://www.theailibrary.co/tool/magicshot"/>')
    info = ailibrary.parse_tool_page(page, "magicshot")
    assert info == {"slug": "magicshot", "name": "MagicShot",
                    "description": "All in one AI image & video generator",
                    "url": "https://www.theailibrary.co/tool/magicshot"}
    with pytest.raises(ValueError):
        ailibrary.tool("../admin")


def test_needle_dataset_answers_execute():
    from sugarcode.llm.dataset import build
    rows, rep = build(per_tool=2, max_tools=40)
    assert rows and rep["tools_covered"] >= 5
    for r in rows[:20]:
        tools = json.loads(r["tools"])
        ans = json.loads(r["answers"])
        assert len(tools) == 4 and ans[0]["name"] in {t["name"] for t in tools}
        assert "error" not in call_tool(ans[0]["name"], ans[0]["arguments"])
        assert r["query"]

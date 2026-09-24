"""Model profiles and an OpenAI-compatible chat client for SugarCode's copilot.

Free-first. The default route is a local open-weight model served by Ollama
on the user's own machine. Hosted routes are opt-in:

* ``inkling`` - Thinking Machines Inkling-Small (Apache-2.0 open weights,
  276B total / 12B active MoE) through the Hugging Face Inference Providers
  router. Needs a free HF token (``HF_TOKEN``); free accounts get monthly
  credits and cannot be billed beyond them without buying credits first.
* ``inkling-self-hosted`` - the same weights on your own vLLM/SGLang server.
* ``fugu`` / ``fugu-ultra`` - Sakana's hosted multi-agent orchestrator. Paid,
  so it needs ``SAKANA_API_KEY`` *and* an explicit allow-paid switch.

Profile fields match the Meemee model layer (name, base_url, model, kind,
api_key_env, requires_key, description, source_url) so all three products
share one configuration vocabulary. Nothing touches the network at import.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

KINDS = ("local", "self_hosted", "hosted_free", "hosted_paid")


class ProviderError(RuntimeError):
    """A profile is misconfigured, gated, or its endpoint failed."""


@dataclass(frozen=True)
class ModelProfile:
    name: str
    base_url: str
    model: str
    kind: str
    api_key_env: str | None = None
    requires_key: bool = False
    description: str = ""
    source_url: str = ""
    base_url_env: str | None = None   # optional override of base_url
    model_env: str | None = None      # optional override of model

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ProviderError(f"profile {self.name!r}: kind must be one of {KINDS}")


BUILTIN_PROFILES: dict[str, ModelProfile] = {p.name: p for p in [
    ModelProfile(
        name="ollama", kind="local",
        base_url="http://localhost:11434/v1", model="qwen2.5:7b-instruct",
        base_url_env="SUGARCODE_OLLAMA_BASE_URL", model_env="SUGARCODE_OLLAMA_MODEL",
        description="Local open-weight model via Ollama. Free, private, runs on your PC.",
        source_url="https://docs.ollama.com/api/openai-compatibility"),
    ModelProfile(
        name="inkling", kind="hosted_free",
        base_url="https://router.huggingface.co/v1", model="thinkingmachines/Inkling-Small",
        api_key_env="HF_TOKEN", requires_key=True,
        base_url_env="SUGARCODE_INKLING_BASE_URL", model_env="SUGARCODE_INKLING_MODEL",
        description=("Thinking Machines Inkling-Small (Apache-2.0 open weights, 276B/12B-active MoE, "
                     "tool calling) via Hugging Face Inference Providers. Free HF token; monthly "
                     "free credits, no billing unless you buy credits."),
        source_url="https://huggingface.co/thinkingmachines/Inkling-Small"),
    ModelProfile(
        name="inkling-flagship", kind="hosted_free",
        base_url="https://router.huggingface.co/v1", model="thinkingmachines/Inkling",
        api_key_env="HF_TOKEN", requires_key=True,
        description=("Flagship Inkling (975B/41B-active) via Hugging Face. Same free credits, "
                     "which it uses up faster."),
        source_url="https://huggingface.co/thinkingmachines/Inkling"),
    ModelProfile(
        name="inkling-self-hosted", kind="self_hosted",
        base_url="", model="thinkingmachines/Inkling-Small",
        api_key_env="SUGARCODE_INKLING_SELF_HOSTED_KEY",
        base_url_env="SUGARCODE_INKLING_SELF_HOSTED_URL", model_env="SUGARCODE_INKLING_SELF_HOSTED_MODEL",
        description="Inkling weights on your own vLLM or SGLang server (set its /v1 URL).",
        source_url="https://huggingface.co/thinkingmachines/Inkling-Small"),
    ModelProfile(
        name="fugu", kind="hosted_paid",
        base_url="https://api.sakana.ai/v1", model="fugu",
        api_key_env="SAKANA_API_KEY", requires_key=True,
        base_url_env="SUGARCODE_FUGU_BASE_URL",
        description="Sakana Fugu multi-agent orchestrator (hosted, paid plans from $20/month).",
        source_url="https://console.sakana.ai/models"),
    ModelProfile(
        name="fugu-ultra", kind="hosted_paid",
        base_url="https://api.sakana.ai/v1", model="fugu-ultra",
        api_key_env="SAKANA_API_KEY", requires_key=True,
        base_url_env="SUGARCODE_FUGU_BASE_URL",
        description="Sakana Fugu Ultra: deeper agent pool for hard problems; slower, paid.",
        source_url="https://console.sakana.ai/models"),
    ModelProfile(
        name="openai-compatible", kind="self_hosted",
        base_url="", model="",
        api_key_env="SUGARCODE_LLM_API_KEY",
        base_url_env="SUGARCODE_LLM_BASE_URL", model_env="SUGARCODE_LLM_MODEL",
        description="Any OpenAI-compatible server: vLLM, llama.cpp server, LM Studio.",
        source_url=""),
]}

DEFAULT_ROUTE = "ollama"


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def load_profiles(env: dict | None = None) -> dict[str, ModelProfile]:
    """Built-in profiles plus custom ones from SUGARCODE_MODEL_PROFILES.

    The variable holds either a JSON list of profile objects or a path to a
    JSON file with that list. Custom profiles may override built-ins by name.
    """
    env = os.environ if env is None else env
    profiles = dict(BUILTIN_PROFILES)
    raw = (env.get("SUGARCODE_MODEL_PROFILES") or "").strip()
    if raw:
        text = raw if raw.startswith("[") else Path(raw).expanduser().read_text()
        try:
            items = json.loads(text)
        except json.JSONDecodeError as e:
            raise ProviderError(f"SUGARCODE_MODEL_PROFILES is not valid JSON: {e}") from e
        allowed = set(ModelProfile.__dataclass_fields__)
        for it in items:
            unknown = set(it) - allowed
            if unknown:
                raise ProviderError(f"custom profile {it.get('name')!r}: unknown fields {sorted(unknown)}")
            p = ModelProfile(**it)
            profiles[p.name] = p
    return profiles


@dataclass
class ChatClient:
    """Minimal OpenAI-compatible chat client (stdlib only)."""

    profile: str
    base_url: str
    model: str
    kind: str
    api_key: str | None = None
    timeout: float = 120.0

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "User-Agent": "sugarcode-ai"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def chat(self, messages: list[dict], tools: list[dict] | None = None,
             temperature: float = 0.1, max_tokens: int = 1024) -> dict:
        body: dict = {"model": self.model, "messages": messages,
                      "temperature": temperature, "max_tokens": max_tokens}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        req = urllib.request.Request(self.base_url.rstrip("/") + "/chat/completions",
                                     data=json.dumps(body).encode(), headers=self._headers(),
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            raise ProviderError(f"{self.profile} HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            reason = getattr(e, "reason", e)
            hint = (f" Is Ollama running? Install from https://ollama.com, then `ollama pull {self.model}`."
                    if self.kind == "local" else "")
            raise ProviderError(f"{self.profile} unreachable at {self.base_url}: {reason}.{hint}") from e
        choices = data.get("choices") or []
        if not choices:
            raise ProviderError(f"{self.profile} returned no choices: {str(data)[:300]}")
        return choices[0].get("message") or {}

    def health(self) -> dict:
        """Zero-token probe: GET {base_url}/models. Never raises."""
        req = urllib.request.Request(self.base_url.rstrip("/") + "/models", headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=min(self.timeout, 15)) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {"profile": self.profile, "ok": False, "error": f"HTTP {e.code}"}
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            return {"profile": self.profile, "ok": False, "error": str(getattr(e, "reason", e))}
        ids = [m.get("id", "") for m in data.get("data", [])]
        out = {"profile": self.profile, "ok": True, "model": self.model,
               "model_listed": self.model in ids, "models_available": len(ids)}
        if "huggingface.co" in self.base_url:
            # the router's /models list is public, so check the token separately
            out["token_valid"] = self._hf_token_valid()
            out["ok"] = out["token_valid"] is True
        return out

    def _hf_token_valid(self) -> bool | str:
        req = urllib.request.Request("https://huggingface.co/api/whoami-v2", headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return bool(json.loads(r.read().decode()).get("name"))
        except urllib.error.HTTPError as e:
            return False if e.code in (401, 403) else f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            return f"unreachable: {getattr(e, 'reason', e)}"


def resolve(name: str | None = None, model: str | None = None, env: dict | None = None,
            allow_paid: bool | None = None) -> ChatClient:
    """Build a client for one profile. Gates: key present; paid needs allow-paid."""
    env = os.environ if env is None else env
    profiles = load_profiles(env)
    name = name or DEFAULT_ROUTE
    if name not in profiles:
        raise ProviderError(f"unknown model profile {name!r}; known: {sorted(profiles)}")
    p = profiles[name]
    base = (env.get(p.base_url_env) if p.base_url_env else None) or p.base_url
    mdl = model or (env.get(p.model_env) if p.model_env else None) or p.model
    key = env.get(p.api_key_env) if p.api_key_env else None
    if not base:
        raise ProviderError(f"{name}: set {p.base_url_env} to your server's /v1 URL")
    if not mdl:
        raise ProviderError(f"{name}: set {p.model_env} or pass --model")
    if p.requires_key and not key:
        how = (" Get a free token at https://huggingface.co/settings/tokens "
               "(fine-grained, permission: 'Make calls to Inference Providers')."
               if p.api_key_env == "HF_TOKEN" else "")
        raise ProviderError(f"{name} needs {p.api_key_env}.{how}")
    if p.kind == "hosted_paid":
        ok = allow_paid if allow_paid is not None else _truthy(env.get("SUGARCODE_ALLOW_PAID"))
        if not ok:
            raise ProviderError(f"{name} is a paid API. Set SUGARCODE_ALLOW_PAID=1 or pass --allow-paid "
                                "to use it; the free defaults are 'ollama' and 'inkling'.")
    return ChatClient(profile=name, base_url=base, model=mdl, kind=p.kind, api_key=key)


def parse_route(env: dict | None = None, route: str | None = None) -> list[str]:
    """Ordered fallback list from SUGARCODE_MODEL_ROUTE (e.g. "inkling,ollama").

    Unknown names fail immediately, so a typo is caught at startup rather than
    on the first question.
    """
    env = os.environ if env is None else env
    raw = route or env.get("SUGARCODE_MODEL_ROUTE") or DEFAULT_ROUTE
    names = [n.strip() for n in raw.split(",") if n.strip()]
    known = load_profiles(env)
    bad = [n for n in names if n not in known]
    if bad:
        raise ProviderError(f"SUGARCODE_MODEL_ROUTE has unknown profiles {bad}; known: {sorted(known)}")
    return names


def resolve_route(env: dict | None = None, route: str | None = None,
                  allow_paid: bool | None = None) -> tuple[list[ChatClient], list[str]]:
    """Clients for every usable profile in the route, plus why others were skipped."""
    clients, skipped = [], []
    for n in parse_route(env, route):
        try:
            clients.append(resolve(n, env=env, allow_paid=allow_paid))
        except ProviderError as e:
            skipped.append(str(e))
    return clients, skipped


def profile_status(env: dict | None = None, probe: bool = False,
                   allow_paid: bool | None = None) -> list[dict]:
    """Every profile with its readiness; `probe=True` also runs the /models health check."""
    env = os.environ if env is None else env
    rows = []
    for p in load_profiles(env).values():
        row = {k: v for k, v in asdict(p).items() if k not in ("base_url_env", "model_env")}
        try:
            c = resolve(p.name, env=env, allow_paid=allow_paid)
            row.update(ready=True, reason="configured", base_url=c.base_url, model=c.model)
            if probe:
                row["health"] = c.health()
        except ProviderError as e:
            row.update(ready=False, reason=str(e))
        rows.append(row)
    return rows

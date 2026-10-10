"""Model profiles and chat clients for SugarCode's copilot.

Free-first. The default route is ``ollama,inkling``: a local open-weight model
on the user's own PC, then Thinking Machines Inkling-Small on the Hugging Face
Inference Providers router when ``HF_TOKEN`` is set. Explicit routes win.

Profile fields and names match the Meemee model layer (name, base_url, model,
kind, transport, api_key_env, requires_key, description, source_url) so all
three products share one configuration vocabulary. See docs/MODELS.md.
Nothing touches the network at import time.
"""
from __future__ import annotations

import importlib.util
import json
import os
import urllib.error
import urllib.request
from dataclasses import MISSING, asdict, dataclass
from pathlib import Path

from .tool_call_codec import DEFAULT_MAX_CHARS, DEFAULT_MAX_DEPTH, ToolCallDecodeError, decode_strict_json

KINDS = ("local", "self_hosted", "hosted_free", "hosted_paid")
TRANSPORTS = ("openai", "transformers")


class ProviderError(RuntimeError):
    """A profile is misconfigured, gated, or its endpoint failed."""


def error_text(exc: BaseException) -> str:
    """H09 AUTHORED, NOT RUN. Text for a ProviderError that is RECORDED OR PRINTED: class name + fixed text, never str(exc).

    ProviderError messages can carry profile/route/custom names, env labels, endpoints and body excerpts (see resolve and
    ChatClient.chat), and a type or subclass says nothing about the message source, so nothing is passed through.
    """
    return f"{type(exc).__name__}: model provider error (details withheld)"


@dataclass(frozen=True)
class ModelProfile:
    name: str
    base_url: str
    model: str
    kind: str
    transport: str = "openai"
    api_key_env: str | None = None
    requires_key: bool = False
    description: str = ""
    source_url: str = ""
    base_url_env: str | None = None
    model_env: str | None = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ProviderError(f"profile {self.name!r}: kind must be one of {KINDS}")
        if self.transport not in TRANSPORTS:
            raise ProviderError(f"profile {self.name!r}: transport must be one of {TRANSPORTS}")


_HF = "https://router.huggingface.co/v1"

BUILTIN_PROFILES: dict[str, ModelProfile] = {p.name: p for p in [
    ModelProfile(
        name="ollama", kind="local", base_url="http://localhost:11434/v1", model="qwen2.5:7b-instruct",
        base_url_env="SUGARCODE_OLLAMA_BASE_URL", model_env="SUGARCODE_OLLAMA_MODEL",
        description="Local open-weight model via Ollama. Free, private, runs on your PC.",
        source_url="https://docs.ollama.com/api/openai-compatibility"),
    ModelProfile(
        name="inkling", kind="hosted_free", base_url=_HF, model="thinkingmachines/Inkling-Small",
        api_key_env="HF_TOKEN", requires_key=True,
        base_url_env="SUGARCODE_INKLING_BASE_URL", model_env="SUGARCODE_INKLING_MODEL",
        description=("Thinking Machines Inkling-Small (Apache-2.0 open weights, 276B total / 12B active "
                     "MoE, tool calling) via Hugging Face Inference Providers. Free HF token; free "
                     "monthly credits, no billing unless you buy credits."),
        source_url="https://huggingface.co/thinkingmachines/Inkling-Small"),
    ModelProfile(
        name="inkling-large", kind="hosted_free", base_url=_HF, model="thinkingmachines/Inkling",
        api_key_env="HF_TOKEN", requires_key=True,
        description="Flagship Inkling (975B / 41B active) via Hugging Face; uses credits faster.",
        source_url="https://huggingface.co/thinkingmachines/Inkling"),
    ModelProfile(
        name="inkling-local", kind="local", base_url="http://localhost:8080/v1", model="inkling-small",
        base_url_env="SUGARCODE_INKLING_LOCAL_URL", model_env="SUGARCODE_INKLING_LOCAL_MODEL",
        description=("Real Inkling-Small on your own machine: Unsloth GGUF served by llama.cpp "
                     "(scripts/inkling/serve_llamacpp.sh). Needs ~89 GB RAM+VRAM at 2-bit, "
                     "~128 GB at 3-bit, 132-170 GB at 4-bit."),
        source_url="https://unsloth.ai/docs/models/inkling"),
    ModelProfile(
        name="inkling-vllm", kind="self_hosted", base_url="http://localhost:8000/v1",
        model="thinkingmachines/Inkling-Small-NVFP4", api_key_env="SUGARCODE_INKLING_VLLM_KEY",
        base_url_env="SUGARCODE_INKLING_VLLM_URL", model_env="SUGARCODE_INKLING_VLLM_MODEL",
        description=("Inkling-Small NVFP4 on a GPU server with vLLM (scripts/inkling/serve_vllm.sh). "
                     "Needs >=180 GB aggregate VRAM: 1x B300, or 2x B200 / 2x H200."),
        source_url="https://recipes.vllm.ai/thinkingmachines/Inkling-Small"),
    ModelProfile(
        name="ornith-local", kind="local", base_url="http://localhost:11434/v1",
        model="hf.co/ornith-ai/Ornith-1.5-9B-GGUF",
        base_url_env="SUGARCODE_ORNITH_BASE_URL", model_env="SUGARCODE_ORNITH_MODEL",
        description=("DeepReinforce Ornith-1.5-9B (MIT, open-source agentic-coding model) as GGUF "
                     "through Ollama: `ollama pull hf.co/ornith-ai/Ornith-1.5-9B-GGUF`."),
        source_url="https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF"),
    ModelProfile(
        name="fugu", kind="hosted_paid", base_url="https://api.sakana.ai/v1", model="fugu",
        api_key_env="SAKANA_API_KEY", requires_key=True, base_url_env="SUGARCODE_FUGU_BASE_URL",
        description="Sakana Fugu multi-agent orchestrator (hosted, paid plans from $20/month).",
        source_url="https://console.sakana.ai/models"),
    ModelProfile(
        name="fugu-ultra", kind="hosted_paid", base_url="https://api.sakana.ai/v1", model="fugu-ultra",
        api_key_env="SAKANA_API_KEY", requires_key=True, base_url_env="SUGARCODE_FUGU_BASE_URL",
        description="Sakana Fugu Ultra (alias of fugu-ultra-v1.1): deeper agent pool; slower, paid.",
        source_url="https://console.sakana.ai/models"),
    ModelProfile(
        name="local-transformers", kind="local", transport="transformers", base_url="in-process",
        model="", model_env="SUGARCODE_TRANSFORMERS_MODEL",
        description=("Any Hugging Face chat model loaded in-process with transformers "
                     "(pip install 'sugarcode-ai[local]'). No server; no tool calling."),
        source_url="https://huggingface.co/docs/transformers"),
    ModelProfile(
        name="openai-compatible", kind="self_hosted", base_url="", model="",
        api_key_env="SUGARCODE_LLM_API_KEY", base_url_env="SUGARCODE_LLM_BASE_URL",
        model_env="SUGARCODE_LLM_MODEL",
        description="Any OpenAI-compatible server: vLLM, SGLang, llama.cpp server, LM Studio."),
]}

DEFAULT_ROUTE = "ollama,inkling"


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def load_profiles(env: dict | None = None) -> dict[str, ModelProfile]:
    """Built-ins plus custom profiles from SUGARCODE_MODEL_PROFILES (JSON list, or a path to one)."""
    env = os.environ if env is None else env
    profiles = dict(BUILTIN_PROFILES)
    raw = (env.get("SUGARCODE_MODEL_PROFILES") or "").strip()
    if raw:
        if raw.startswith("["):
            text = raw
        else:
            try:
                text = Path(raw).expanduser().read_text()
            except (OSError, ValueError) as e:  # missing/unreadable file, bad bytes, NUL in the path
                raise ProviderError(f"SUGARCODE_MODEL_PROFILES file could not be read ({type(e).__name__})") from None
        try:
            items = decode_strict_json(text, DEFAULT_MAX_CHARS, DEFAULT_MAX_DEPTH, root="array")
        except ToolCallDecodeError as e:  # reason only; the input is never echoed
            raise ProviderError(f"SUGARCODE_MODEL_PROFILES is not a valid strict JSON list: {e.reason}") from None
        allowed = set(ModelProfile.__dataclass_fields__)
        required = sorted(n for n, f in ModelProfile.__dataclass_fields__.items()
                          if f.default is MISSING and f.default_factory is MISSING)
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                raise ProviderError(f"SUGARCODE_MODEL_PROFILES item {i} must be a JSON object")
            unknown = set(it) - allowed
            if unknown:
                raise ProviderError(f"SUGARCODE_MODEL_PROFILES item {i}: unknown fields {sorted(unknown)}")
            missing = [n for n in required if n not in it]
            if missing:
                raise ProviderError(f"SUGARCODE_MODEL_PROFILES item {i}: missing fields {missing}")
            # Failures are recorded inside the except blocks and raised AFTER them, so the raised
            # ProviderError has no __context__/__cause__ holding the constructor's exception (whose
            # message can carry the profile name).
            p, shadows, failure = None, False, None
            try:
                p = ModelProfile(**it)
                shadows = p.name in BUILTIN_PROFILES
            except ProviderError:  # __post_init__ messages include self.name; never forwarded
                failure = "invalid kind or transport"
            except TypeError:
                failure = "invalid field values"
            if failure is not None:
                raise ProviderError(f"SUGARCODE_MODEL_PROFILES item {i}: {failure}")
            if shadows:
                raise ProviderError(f"SUGARCODE_MODEL_PROFILES item {i}: {p.name!r} is a built-in profile name and cannot be replaced")
            try:
                profiles[p.name] = p
            except TypeError:
                failure = "invalid profile name"
            if failure is not None:
                raise ProviderError(f"SUGARCODE_MODEL_PROFILES item {i}: {failure}")
    return profiles


class _WhoamiMalformed:
    """Internal signal from _hf_token_valid: a 200 whoami body of the wrong shape (type names only, no body)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason


@dataclass
class ChatClient:
    """OpenAI-compatible chat client (stdlib only)."""

    profile: str
    base_url: str
    model: str
    kind: str
    api_key: str | None = None
    timeout: float = 120.0
    supports_tools = True

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
            raise ProviderError(f"{self.profile} HTTP {e.code}: {e.read().decode(errors='replace')[:400]}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            hint = (f" Is the local server running? For Ollama: install from https://ollama.com, "
                    f"then `ollama pull {self.model}`.") if self.kind == "local" else ""
            raise ProviderError(f"{self.profile} unreachable at {self.base_url}: "
                                f"{getattr(e, 'reason', e)}.{hint}") from e
        except ValueError as e:  # bad JSON / UnicodeDecodeError / int digit limit in the response body
            raise ProviderError(f"{self.profile} returned an unreadable response: {str(e)[:200]}") from e
        if not isinstance(data, dict):
            raise ProviderError(f"{self.profile} returned a {type(data).__name__} body, expected an object")
        choices = data.get("choices") or []
        if not choices:
            raise ProviderError(f"{self.profile} returned no choices: {str(data)[:300]}")
        if not isinstance(choices, list):
            raise ProviderError(f"{self.profile} returned choices of type {type(choices).__name__}, expected a list")
        first = choices[0]
        if not isinstance(first, dict):
            raise ProviderError(f"{self.profile} returned a first choice of type {type(first).__name__}, expected an object")
        message = first.get("message")
        if message is None:
            return {}
        if not isinstance(message, dict):
            raise ProviderError(f"{self.profile} returned a message of type {type(message).__name__}, expected an object")
        return message

    def health(self) -> dict:
        """Zero-token probe: GET {base_url}/models (plus an HF token check on the HF router).

        Returns an error result {profile, ok: False, error} instead of raising for: an HTTP, URL, OS, timeout or
        value error on /models; a /models body of the wrong shape; and a malformed whoami body on the HF router.
        No claim is made about any other exception. chat() differs: it raises ProviderError.
        """
        req = urllib.request.Request(self.base_url.rstrip("/") + "/models", headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=min(self.timeout, 15)) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {"profile": self.profile, "ok": False, "error": f"HTTP {e.code}"}
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            # H09: OS/network reason text can carry host/endpoint details; class name only (HTTP code above is an int)
            return {"profile": self.profile, "ok": False, "error": f"unreachable: {type(e).__name__}"}
        if not isinstance(data, dict):  # valid JSON of the wrong shape: an error RESULT, never a raise (chat() raises instead)
            return {"profile": self.profile, "ok": False,
                    "error": f"malformed /models response: body is {type(data).__name__}, expected an object"}
        members = data.get("data", [])
        if not isinstance(members, list):
            return {"profile": self.profile, "ok": False,
                    "error": f"malformed /models response: data is {type(members).__name__}, expected a list"}
        if not all(isinstance(m, dict) for m in members):
            return {"profile": self.profile, "ok": False,
                    "error": "malformed /models response: data has a member that is not an object"}
        ids = [m.get("id", "") for m in members]
        out = {"profile": self.profile, "ok": True, "model": self.model,
               "model_listed": self.model in ids, "models_available": len(ids)}
        if "huggingface.co" in self.base_url:
            token = self._hf_token_valid()  # the router's model list is public
            if isinstance(token, _WhoamiMalformed):
                return {"profile": self.profile, "ok": False, "error": f"malformed whoami response: {token.reason}"}
            out["token_valid"] = token
            out["ok"] = token is True
        return out

    def _hf_token_valid(self) -> "bool | str | _WhoamiMalformed":
        req = urllib.request.Request("https://huggingface.co/api/whoami-v2", headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return False if e.code in (401, 403) else f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            return f"unreachable: {type(e).__name__}"  # H09: class only, reason text withheld
        if not isinstance(data, dict):
            return _WhoamiMalformed(f"body is {type(data).__name__}, expected an object")
        name = data.get("name")
        if isinstance(name, str) and name != "":  # whitespace-only counts as non-empty; no strip
            return True
        return _WhoamiMalformed("name is missing or not a non-empty string")


@dataclass
class TransformersClient(ChatClient):
    """In-process generation with Hugging Face transformers (optional dependency). No tool calling."""

    supports_tools = False

    def __post_init__(self):
        self._pipe = None

    def chat(self, messages, tools=None, temperature=0.1, max_tokens=1024):
        if self._pipe is None:
            try:
                from transformers import pipeline  # type: ignore
            except ImportError as e:
                raise ProviderError("local-transformers needs `pip install 'sugarcode-ai[local]'`") from e
            self._pipe = pipeline("text-generation", model=self.model)
        out = self._pipe(messages, max_new_tokens=max_tokens, do_sample=temperature > 0,
                         temperature=max(temperature, 1e-5), return_full_text=False)
        text = out[0]["generated_text"]
        if isinstance(text, list):
            text = text[-1].get("content", "")
        return {"role": "assistant", "content": text}

    def health(self) -> dict:
        ok = importlib.util.find_spec("transformers") is not None
        return {"profile": self.profile, "ok": ok, "model": self.model,
                **({} if ok else {"error": "transformers not installed"})}


def resolve(name: str | None = None, model: str | None = None, env: dict | None = None,
            allow_paid: bool | None = None) -> ChatClient:
    """Client for one profile. Gates: key present; hosted_paid also needs allow-paid."""
    env = os.environ if env is None else env
    profiles = load_profiles(env)
    name = name or DEFAULT_ROUTE.split(",")[0]
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
        how = (" Get a free token at https://huggingface.co/settings/tokens (fine-grained, "
               "permission 'Make calls to Inference Providers')." if p.api_key_env == "HF_TOKEN" else "")
        raise ProviderError(f"{name} needs {p.api_key_env}.{how}")
    if p.kind == "hosted_paid":
        ok = allow_paid if allow_paid is not None else _truthy(env.get("SUGARCODE_ALLOW_PAID"))
        if not ok:
            raise ProviderError(f"{name} is a paid API. Set SUGARCODE_ALLOW_PAID=1 or pass --allow-paid; "
                                "the free defaults are 'ollama' and 'inkling'.")
    cls = TransformersClient if p.transport == "transformers" else ChatClient
    return cls(profile=name, base_url=base, model=mdl, kind=p.kind, api_key=key)


def parse_route(env: dict | None = None, route: str | None = None) -> list[str]:
    """Ordered fallback from `route` or SUGARCODE_MODEL_ROUTE. Unknown names fail at startup."""
    env = os.environ if env is None else env
    raw = route or env.get("SUGARCODE_MODEL_ROUTE") or DEFAULT_ROUTE
    names = [n.strip() for n in raw.split(",") if n.strip()]
    known = load_profiles(env)
    bad = [n for n in names if n not in known]
    if bad:
        raise ProviderError(f"model route has unknown profiles {bad}; known: {sorted(known)}")
    return names


def resolve_route(env: dict | None = None, route: str | None = None,
                  allow_paid: bool | None = None) -> tuple[list[ChatClient], list[str]]:
    """Clients for each usable profile in route order, plus reasons for the skipped ones."""
    clients, skipped = [], []
    for n in parse_route(env, route):
        try:
            clients.append(resolve(n, env=env, allow_paid=allow_paid))
        except ProviderError as e:
            skipped.append(error_text(e))  # H09: no profile name / env label / endpoint text
    return clients, skipped


def profile_status(env: dict | None = None, probe: bool = False,
                   allow_paid: bool | None = None) -> list[dict]:
    """Every profile with readiness (configuration only unless probe=True)."""
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
            row.update(ready=False, reason=error_text(e))  # H09
        rows.append(row)
    return rows

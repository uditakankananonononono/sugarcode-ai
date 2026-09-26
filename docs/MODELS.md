# SugarCode model layer

`src/sugarcode/llm/` connects SugarCode's 88 modules to chat models. A question goes
through a trained router, which picks the relevant modules. Their functions are offered
to the model as tools, the model calls them, and the real module code computes the
numbers. Free-first: nothing paid runs unless you switch it on.

## Quick start

```bash
pip install -e .
sugarcode models list            # every profile and whether it is configured
sugarcode models check           # zero-token health probe of the active route
sugarcode route "score off-target risk for this sgRNA"   # trained router only, no model needed
sugarcode ask "codon optimize MKTAYIAKQRQ for E. coli"     # full copilot
```

## Model profiles

| Profile | Kind | What it is | Needs |
|---|---|---|---|
| `ollama` (default) | local | Any open-weight model in Ollama, default `qwen2.5:7b-instruct` | [Ollama](https://ollama.com) running |
| `inkling` | hosted_free | Thinking Machines **Inkling-Small** (Apache-2.0, 276B total / 12B active MoE, tool calling) on the Hugging Face Inference Providers router | `HF_TOKEN` |
| `inkling-large` | hosted_free | Flagship Inkling (975B / 41B active) on the same router | `HF_TOKEN` |
| `inkling-local` | local | Real Inkling-Small on your own machine, Unsloth GGUF via llama.cpp | ~89 GB RAM+VRAM (2-bit) |
| `inkling-vllm` | self_hosted | Inkling-Small NVFP4 on a GPU server with vLLM | >=180 GB VRAM |
| `ornith-local` | local | DeepReinforce **Ornith-1.5-9B** (MIT, agentic coding) GGUF via Ollama | `ollama pull hf.co/ornith-ai/Ornith-1.5-9B-GGUF` |
| `fugu` / `fugu-ultra` | hosted_paid | Sakana Fugu multi-agent API (paid plans) | `SAKANA_API_KEY` + `SUGARCODE_ALLOW_PAID=1` |
| `local-transformers` | local | Any HF chat model in-process (no tool calling) | `pip install -e .[local]`, `SUGARCODE_TRANSFORMERS_MODEL` |
| `openai-compatible` | self_hosted | Any OpenAI-compatible server | `SUGARCODE_LLM_BASE_URL`, `SUGARCODE_LLM_MODEL` |

Route: `SUGARCODE_MODEL_ROUTE` is an ordered fallback list. Default `ollama,inkling`:
local first, then Inkling on the HF router when `HF_TOKEN` is set. Unknown names fail at
startup. Custom profiles: `SUGARCODE_MODEL_PROFILES` holds a JSON list (or a path to one)
using the same fields as the built-ins.

Profile fields match the Meemee model layer: `name, base_url, model, kind
(local|self_hosted|hosted_free|hosted_paid), transport (openai|transformers), api_key_env,
requires_key, description, source_url`. Env mapping: Sugarcode `HF_TOKEN` = Meemee
`MEEMEE_HF_TOKEN`; Sugarcode `SAKANA_API_KEY` = Meemee `MEEMEE_FUGU_API_KEY`.

## Inkling

**Working today (free):** create a free Hugging Face account, then a token at
https://huggingface.co/settings/tokens (fine-grained, permission "Make calls to Inference
Providers"). `export HF_TOKEN=hf_...` and `sugarcode models check inkling` should show
`"ok": true`. Free accounts get $0.10/month of Inference Providers credit (per
https://huggingface.co/docs/inference-providers/pricing). Extra usage needs purchased
credits, so a free token can run out but cannot be billed by surprise. Inkling-Small costs
about $0.50 input / $1.20 output per million tokens on the router's cheapest provider, so
the free credit is small.

**On your own PC (real Inkling-Small, quantized):** `scripts/inkling/serve_llamacpp.sh`
builds llama.cpp and serves `unsloth/Inkling-Small-GGUF`. Memory needed, RAM + VRAM
combined (https://unsloth.ai/docs/models/inkling): 2-bit ~89 GB, 3-bit ~128 GB, 4-bit
132-170 GB. Then `SUGARCODE_MODEL_ROUTE=inkling-local`.

**On a GPU server:** `scripts/inkling/serve_vllm.sh` runs the vLLM recipe
(https://recipes.vllm.ai/thinkingmachines/Inkling-Small): NVFP4 needs >=180 GB aggregate
VRAM (1x B300, or 2x B200 / 2x H200). Then set `SUGARCODE_INKLING_VLLM_URL`.

**Fine-tuning Inkling itself** needs Thinking Machines' Tinker service (paid) or 180 GB+
of GPU memory. It is not run here.

## Training on SugarCode's own data

1. **Module router** (trained, shipped). TF-IDF + softmax regression over each module's
   spec, registry summary and function docstrings. Retrain: `python scripts/train_router.py`.
   Held-out numbers are in `src/sugarcode/llm/data/router_report.json`: top-3 67% on held-out
   passages vs 5% majority baseline. It ties, but does not beat, an untrained
   nearest-centroid baseline (70%).
2. **Needle tool-caller** (dataset shipped, fine-tune runs on your PC).
   `python scripts/build_needle_dataset.py` writes `data/needle/sugarcode_tools.jsonl` in the
   format [cactus-compute/needle](https://github.com/cactus-compute/needle) fine-tunes on.
   Each example is a real module call that was executed and succeeded, with 3 distractor
   tools. Queries are template-generated. Then `needle finetune data/needle/sugarcode_tools.jsonl`.

## AI Library connector

`sugarcode ailibrary search "code"` and `sugarcode ailibrary tool <slug>` read The AI
Library's public tool directory (https://www.theailibrary.co) from its sitemap and tool
pages, cached for a day and rate-limited. Read-only: it never submits or lists anything.
Search matches words in tool slugs only.

## Sources checked

- Sakana Fugu model IDs: https://console.sakana.ai/models (`fugu`, `fugu-ultra` = v1.1)
- Inkling-Small: https://huggingface.co/thinkingmachines/Inkling-Small
- Ornith: https://github.com/deepreinforce-ai/ornith-1, https://huggingface.co/ornith-ai
- Needle: https://github.com/cactus-compute/needle

## Shared model layer (instinct_models)

SugarCode runs on the same model layer as Atlas and Meemee:
https://github.com/uditakankananonononono/shared-models, vendored at `src/instinct_models/`
(pinned commit in `src/instinct_models/VENDORED.md`, re-vendor with `scripts/vendor_instinct_models.sh <commit>`).

- `sugarcode shared ask "question" [--private] [--no-execute]`: the trained module router picks
  SugarCode tools. The shared Router then tries Needle (on-device), Ornith (local), Inkling local, and
  the Inkling HF router in that order. The chosen call runs against the real module. `--private` never uses the hosted route.
  Calls to tools that were not offered are refused.
- `sugarcode shared dataset out.jsonl`: SugarCode's Needle LoRA dataset through the shared pipeline.
  Synthetic queries, each answer verified by executing it, plus about 1 in 8 off-topic rows. No user data.
- Env: `INSTINCT_PRODUCT=sugarcode` (default), `INSTINCT_INKLING_LOCAL_URL`, `INSTINCT_INKLING_LOCAL_MODEL`,
  `INSTINCT_ORNITH_URL`, `INSTINCT_ORNITH_MODEL`, `INSTINCT_NEEDLE_WEIGHTS`, `INSTINCT_ALLOW_HOSTED`, `HF_TOKEN`.
- Fugu (paid) is not in the shared layer. It stays in `sugarcode.llm.providers` behind `SUGARCODE_ALLOW_PAID`.
- Jev (TypeSafe AI's hosted "System One" evaluation model, https://thejevai.com) is available through
  `sugarcode.llm.shared.shared_jev()`: it evaluates one state against typed questions (choice / score / noul)
  and returns structured decisions with probabilities. It is NOT a chat model, so it is not a model profile
  and never joins `SUGARCODE_MODEL_ROUTE`. It is key-gated and paid (credits,
  https://thejevai.com/pricing - no free tier as of 2026-09-26; also listed on the Vercel AI Gateway as
  `typesafe-ai/jev`), and it is OFF unless a key is set (`INSTINCT_JEV_API_KEY` or `JEV_API_KEY`; create one
  at https://thejevai.com/settings/apikeys). Hosted route: never send it private state - keep sequences on
  the local routes.

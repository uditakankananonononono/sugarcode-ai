# Module self-improvement engine

Every Sugarcode module (all 95+ under `sugarcode.modules`) can extend
itself: it detects its own capability gaps, synthesizes a new feature as
real Python code, writes and runs tests for it in a sandbox, and - only
after a human approves - activates it into its own feature registry.

## Pipeline

1. **Report** - `engine.record_gap("filter only pathogenic variants",
   exemplar=...)`; events persist as append-only JSONL.
2. **Detect** - recurring signatures become `CapabilityGap`s
   (`min_occurrences`, default 2).
3. **Plan** - `FeaturePlanner` maps the gap to one of six capability kinds
   (`keyword_filter`, `scoring_rule`, `text_transform`, `aggregator`,
   `threshold_alert`, `field_extractor`). An optional `ProposalRefiner`
   (e.g. the shared local model layer) can enrich plans but cannot widen
   the kind whitelist.
4. **Synthesize** - deterministic template codegen plus a generated pytest
   suite; every byte passes the static safety scanner (import allowlist,
   no exec/eval/open, no dunder access, no async).
5. **Evaluate** - tests run in a subprocess sandbox with a scrubbed
   environment and hard timeout. Failing candidates die here.
6. **Propose** - passing candidates persist with sha256 digests and an
   approval request is filed in the manual gate.
7. **Activate** - only with an approved decision matching the candidate's
   own approval id. The feature file lands in the module's `extensions/`
   dir and is recorded in `registry.json`.
8. **Dispatch** - `engine.dispatch(name, items)` re-verifies the file's
   sha256 on every call; tampered features refuse to run.
9. **Rollback** - approval-gated, restores the previous active version.

## Autonomy boundary

Detection, planning, code writing, and testing are autonomous. Activation
and rollback require a human decision recorded in the gate
(`ManualApprovalGate`, file-backed). The engine never edits module source
code; features live only in the module's own state directory.

## Usage

```python
from sugarcode.self_improve import attach_all

engines = attach_all()                      # one engine per module
engine = engines["acmg_bayesian"]
engine.record_gap("filter only pathogenic variants", exemplar="...")
report = engine.run_cycle()                 # autonomous up to the gate
# human approves the request id in the gate file, then:
engine.activate(report["proposals"][0]["key"],
                approval_id=report["proposals"][0]["approval_id"])
engine.dispatch(report["proposals"][0]["name"], ["BRCA1 pathogenic variant"])
```

## Configuration

- `SUGARCODE_SELF_IMPROVE_HOME` - state root (default
  `~/.sugarcode/self_improve`).
- Free-first: no model, network, or paid API required anywhere in the loop.

## Tests

`tests/self_improve/` - 34 tests covering detection, planning, codegen,
safety scanning, sandboxing, registry integrity, the full engine cycle,
the mixin, and wiring across every module in `sugarcode.modules`.

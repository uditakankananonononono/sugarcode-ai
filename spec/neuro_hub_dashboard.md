> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# Neuro-Hub (Dashboard)

Neuro-Hub (Dashboard): The central command center for SugarCode AI. It monitors global compute flux and provides a unified search interface across the 84-node neural stack. Users can visualize platform-wide health, access recent project states, and initiate high-fidelity biological searches, serving as the gateway to the entire digital-biological operating system.

## Whole-claim corrections (2026-10-12, stack B7)

These corrections apply to the original wording above. They describe the
implementation in src/sugarcode/modules/neuro_hub_dashboard/core.py and do not
claim that the aspirational capability has been implemented.

- S5-064.01, original claim: "The central command center for SugarCode AI".
  Corrected scope (OVERSTATED): An aggregation dashboard over the module registry (health counts, stored project states, search). It issues no commands and controls nothing.
- S5-064.02.C01, original claim: "global compute flux".
  Corrected scope (OVERSTATED): compute_flux_series derives online/total availability ratios from caller-supplied samples; no compute load anywhere is instrumented, so no compute flux is measured.
- S5-064.02.C02, original claim: "unified search interface".
  Corrected scope (SCOPED): unified_search does whole-token count search over caller-supplied module records.
- S5-064.02.C03, original claim: "84-node neural stack".
  Corrected scope (UNSUPPORTED): No neural stack exists in this codebase; the registry holds 95 conventionally computed modules.
- S5-064.03.C01, original claim: "platform-wide health".
  Corrected scope (SCOPED): platform_health imports each registered module and reports the online count and per-module status.
- S5-064.03.C02, original claim: "recent project states".
  Corrected scope (SCOPED): project_state returns stored per-project stage/updated/summary records.
- S5-064.03.C03, original claim: "high-fidelity biological searches".
  Corrected scope (UNSUPPORTED): Search is whole-token counting over caller-supplied text; no biological index, ranking model or fidelity notion exists.

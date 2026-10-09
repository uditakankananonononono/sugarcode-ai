# Experimental task-distinct gap priority preview

Build hypothesis: a recurring-task failure should be ranked by distinct tasks,
not raw repeated log entries. Preserve development and held-out evidence as
separate counts so development passes do not erase held-out failures.

This is a new SugarCode combination, not a proven new research method or AGI.
Prior art includes failure clustering, fault-localization prioritization and
repair overfitting detection. No claim of global originality is made.

API: SelfImprovementEngine.preview_gap_evidence accepts explicit GapObservation
records and returns a deterministic read-only priority table. Rank is
lexicographic: held-out failed tasks, then development failed tasks, then
signature. This ordering is a hand-chosen heuristic, not learned confidence.
A task ID has exactly one partition across the preview; contradictory outcomes
within one gap/task are refused. Version task IDs for new runs. Repeated rows
increase the visible observation count but not the priority task count. All
unique source references survive in sorted order. IDs/references are caller
claims, not authenticated evidence. A caller can inflate distinct IDs or label
training tasks held-out; no provenance or independence proof is implied.

Limits: at most 10,000 observations, identifiers at most 512 characters. The
preview does not change raw gap detection, planning, synthesis, approval,
execution, registry or ledger. It is not persistence, counterexample replay,
auto-repair, outcome measurement or model evaluation. Tests use synthetic
records, not real task outcomes. A next experiment would compare ranking
against current recurrence counts using independently labeled historical tasks.
No benefit is claimed until that experiment is done.

Prior-art sources inspected on 2026-10-09:
- https://dl.acm.org/doi/10.1145/2786805.2786825 : independent-test repair overfitting.
- https://dl.acm.org/doi/10.1145/3092703.3092718 : DiffTGen overfitting tests.
- https://dl.acm.org/doi/10.1145/2491509.2491513 : fault localization prioritization.
- https://ar5iv.labs.arxiv.org/html/2104.10360 : failure clustering with hypergraphs.
- https://arxiv.org/abs/2403.05022 : probabilistic/grouped fault localization.
- https://arxiv.org/html/2511.16858v1 : LLM program-repair test overfitting preprint.
These papers' reported results were not reproduced for this feature.

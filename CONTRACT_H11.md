# CONTRACT_H11 - neohunter ridge PSSM provenance/honesty metadata (AUTHORED, NOT RUN)

Parent: 1463a9201bff0c90c321ab43ebd64535d1d52ac5 (public HEAD readback 15:33 IST, equal; peer-reported landing). Authority: Main's relays of peer rulings, not independently authenticated by me. Nothing was run: no pytest, import, compile, trainer or runtime.

## Lead and source proof (read)
scripts/train_neohunter_pssm.py (blob 9b50df46): fits ~80% (`w = fit(X[~test], y[~test])`), metrics from that fit, then `wf = fit(X, y)` on ALL rows; one stored record mixes the 80%-fit r/AUC with the all-row weights. n_train_total = len(rows) (all rows incl. held-out). core.py hla_binding_trained returns heldout_* next to predictions from the all-row weights. Tests (test_neohunter_honesty.py) assert only thresholds, never that metrics match the shipped model.

## Changes (documentary only; no weight or per-allele numeric change)
1. core.py: `metrics_caveat` key with the peer-approved text VERBATIM: "stored held-out r/AUC describe the 80%-fit model, not the shipped all-row model; stored source values, not validated performance". Docstring WARNING added. All existing keys kept (no API break). hla_binding passes it through for 9-mers; the 8/10/11-mer heuristic result is unchanged (no caveat key).
2. data_pssm_iedb2013.json: TOP-LEVEL ONLY, textual insertion, alleles block untouched: fit_all_rows true; metrics_describe_model "80pct-fit"; split_description "about 20% held out; exact split not reproducible from available artifacts"; n_train_total_semantics (n_train_total counts ALL rows incl. n_heldout; metrics from a fit on the remaining rows; weights refit on all rows); near_neighbour_note (the ~12% A*02:01 claim attributed to STATUS.md:750 as stated there, not reproduced here). No invented numbers.
3. trainer: for a FUTURE regeneration only (not run): top-level refit_all_rows, metrics_describe_model, split_description, n_train_total_semantics; per-allele metric_fit_size = int((~test).sum()). n_train_total not renamed.
4. tests/test_h11_neohunter_provenance.py (new): pins JSON top-level keys, notes, per-allele key set and the five stored (n_train_total, n_heldout, r, AUC) tuples unchanged, weights shape, caveat text and key retention, heuristic has no caveat, docstring warning, trainer source text (text read only).

## Judgement calls flagged (not relayed)
- (SUPERSEDED by H11f below) Name: the ruling listed "refit_all_rows" for the trainer and "fit_all_rows" for the JSON; I used `fit_all_rows` in both so regenerated JSON matches the shipped one.
- Trainer split_description states the script's actual rule (md5(peptide) % 5 == 0, about 20%), the JSON carries the approved "not reproducible" wording because the data file is unavailable. They differ on purpose; say if you want them equal.
- Trainer adds per-allele metric_fit_size (future regeneration); the shipped JSON does NOT get it (per-allele numeric edit not allowed). Regenerated JSON would therefore differ in shape from the shipped one until regenerated.
- Added JSON top-level keys n_train_total_semantics and near_neighbour_note beyond the three relayed examples; both are text, source-attributed.

## Out of scope / findings
iedb_pssm_9mer.json and hla_binding_iedb (separate logistic model) excluded. A future major-version rename/qualification of heldout_* keys is a finding only. Stored r/AUC are stored source values, not validated performance; no PASS claim.

## Chronology (IST)
15:33:53 tests/test_h11_neohunter_provenance.py written first; 15:34:01 done. 15:34:10 trainer, JSON, core.py edited (one docstring line reflow after, so the phrase sits on one line for the test). Then this contract.

## Read depth
Verbatim: train_neohunter_pssm.py (58), test_neohunter_honesty.py (39), core.py 1-75 and 370-387, JSON top-level and per-allele scalars (weights shape checked structurally only, values not read), STATUS.md:750. Grep-only: core.py 75-369 (consumers: find_neoantigens, immunogenicity use ["score"]), repo callers. Not read: other neohunter tests, spec/neohunter.md.
Blob pins at base: trainer 9b50df46, core.py 7c99a939, JSON 8f2ecd2d, honesty test 6d59cddf, STATUS.md e4a1bc30 (all re-verified at 1463a920).

## RUN vs NOT RUN
RUN: git/diff/sha tooling, a read-only JSON parse in the editing script to confirm alleles block equal before/after. NOT RUN: pytest, imports, trainer. Unverified: all new tests, the JSON stays valid beyond that one parse.

## Claim limit
Authored only; not tested, not working; no general privacy or performance claim.

## H11f follow-up (stacked on 427afd1a; original H11 history preserved)
Authority: Main's relays of peer H11 adjudications, not independently authenticated by me. Read-gate deviation in the original H11 is NOTED and not excused; core.py 75-369 is now read line by line (find_neoantigens, _vaccine, find_neoantigens_live, _gnomad_specificity, translate_variants, proteasomal_processing, structural_mhc_binding, immunogenicity_profile, simulate_immune_escape, optimize_vaccine_panel, _neo_diagnostics, neoantigen_pipeline). Only hla_binding(...)["score"/"class"/"hla"] is consumed outside hla_binding_trained; nothing reads heldout_* or metrics_caveat. Observation, finding only: _neo_diagnostics carries "binding_model_status": "deterministic, untrained, not clinically validated" while 9-mer scores come from the trained ridge matrix; not touched. Weights: shape checked structurally, numeric weight values not read.
TWO DISTINCT FLAGS, both documented:
- `fit_all_rows: true` in the SHIPPED JSON = weight origin: the shipped weights/bias were fit on all rows (source: trainer line `wf = fit(X, y)`; docstring lines 6-8).
- `refit_all_rows` in the TRAINER output = a PROCESS flag for a FUTURE regeneration: the trainer refits on all rows after the 80% metric fit. Trainer field renamed fit_all_rows -> refit_all_rows (metadata key only; no trainer logic changed). Regenerated JSON would therefore carry refit_all_rows where the shipped file carries fit_all_rows until the peer decides otherwise.
split_description, EXACT peer text in both trainer and JSON: "split algorithm md5%5 known from trainer code; the shipped instance is not reproducible from available artifacts". The earlier text "about 20% held out; exact split not reproducible..." is replaced. Algorithm (md5(s.encode()) hex int % 5 == 0, trainer line 43) is code-verifiable; the instance behind the shipped numbers is not reproduced (IEDB data not in repo).
Tests changed FIRST (15:36:34-45): SPLIT exact in JSON and trainer text, trainer needle refit_all_rows and no "fit_all_rows" literal, JSON keeps fit_all_rows true and has no refit_all_rows, contract mentions both. Then trainer/JSON edits (15:36:51), then this section. No weight or numeric change. Nothing run (a read-only json.load of the JSON succeeded). Claim limit unchanged: authored only.

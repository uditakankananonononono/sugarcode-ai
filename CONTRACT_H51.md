# H51 one direct atom B-factor filter literal

Parentbf1c93811db53aecbeec6fea0cd72751282ed707.
One test+contract additions only. No source/old-test edits, parser,
model-selection, structure accuracy, range semantics or biology claim.
Actual API is module-level sugarcode.bio.pdb.select, not PDBModel.select.
Parent's incorrect class/method name and new 'CONTRACT GATE' wording were
corrected before authoring; established test-first workflow retained.

## Visible gate (2026-10-10 IST)
Full pdb.py1-346, bio_pdb1-137 and cli_pdb1-38 visibly read22:08:19;
full CIF-real1-40, CLI consumers737-780, repository min_bfactor/residues
coverage search inspected22:08:26. No min_bfactor test found in that search.
Source414d4eae7509dde0eebf8b19e8f4a1ccaa8f67dc;
direct87a22674191472d7b0594459830b2624c26b6603;
CLI5c9aa91d2b785dda62b316b342628782cbfa48d6.
Ratified22:08:30, naming/flow clarification22:08:40. Fresh public fetch
verified exact parent, relevant255-279 visibly re-read before test22:08:46.
Test first, execution next, contract after. Documentary chronology, not
independent proof of comprehension. Full read excludes unrelated consumers.

## Exact scope
Supplied structure atoms serial1/model1/bfactor9, serial2/model1/bfactor10,
serial3/model1/bfactorNone. select(...,min_bfactor10) gives serials[2].
Equality retained, missing and below excluded in this one literal. Existing
query tests cover name/record/chain and default model1, not B-factor threshold.
No metadata, general output-order/copy/identity or model-policy claim.
No PDB/mmCIF parse, file or external observed atom data used.

## Author execution
New1 PASS0.12s; new+bio_pdb+cli_pdb+CIF-real:14 PASS0.86s;
self_improve+same4files1854 PASS/13 XFAIL39.62s, not global suite.
Four temporary mutants each1F: exclusive <=; missing allowed; numeric
threshold ignored; filter disabled. Source restored byte-exact, src diff
clean, restored new1 PASS0.10s. Independent audit/exact EXECUTE before landing.

## Contract-only correction before transfer
Initial local candidate1c166731f6b93502483784bfcf27d1509532a981 wrongly
stated line totals358/143/40/43. Actual wc totals346/137/38/40; full files
were read, but guessed counts were wrong. Replaced on the same parent,
not stacked; test bytes unchanged. Initial candidate not delivered/landed.

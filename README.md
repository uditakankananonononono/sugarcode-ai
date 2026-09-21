# SugarCode AI

A multi-omic bio-design platform organized as a network of specialized modules on the
**Omega OS v7.0** framework. Built line-by-line from the SugarCode AI spec doc
(`spec/` holds the full per-module spec corpus extracted from the source document).

## Architecture

```
src/omega/            Omega OS v7.0 framework
  registry.py         All 77 modules + 9 sub-networks + lifecycle status
  health.py           Per-module import/self-test health, global compute flux
  search.py           Unified BM25-style biological search over the module corpus
  api.py              FastAPI surface (/modules /subnetworks /health /search)
src/sugarcode/
  bio/                Shared scientific toolkit: sequence ops, FASTA, codon
                      usage/CAI, position weight matrices
  modules/<slug>/     One package per module
tests/                pytest suite - one named test per public behavior
spec/                 The spec doc split into 77 module spec files + index
```

## Sub-networks (9)

The source doc states "nine functional sub-networks" without naming them; these
assignments are derived from module themes:

| Sub-network | Modules |
|---|---|
| core-intelligence | 6 |
| genome-editing | 13 |
| protein-engineering | 5 |
| synthetic-biology | 12 |
| cellular-systems | 11 |
| therapeutics | 13 |
| microbiome-phage | 7 |
| fabrication-evolution | 6 |
| platform | 4 |

## Build status ledger (honest counts)

The spec's own counts are internally inconsistent: the intro says **78** modules,
Neuro-Hub's text says an "**84-node** neural stack". **77 modules are actually
specified** in the document; all 77 are registered and spec-filed. We build and
count against the 77 that exist, not the 78/84 claimed.

Status per module: **verified** = implemented with passing named tests;
**thin** = partial implementation; **specified** = spec captured, implementation pending.

| Drop | Verified | Thin | Specified (pending) | Tests |
|---|---|---|---|---|
| 1 (this drop) | 16 | 0 | 61 | 51 passing |

### Verified in this drop (real implementations, named tests)

| Module | What is real |
|---|---|
| neuro_hub | dashboard aggregation over live health + unified search + project store |
| gene_explorer | full central dogma: transcription, translation, ORFs, MW, hydrophobicity, animation keyframes |
| crispr_opt | PAM enumeration both strands, GC 40-60% filter, position-weighted on-target score, seed-weighted off-target scan, hairpin check, browser-track payload |
| codon_opt | CAI optimization vs E. coli K12 / H. sapiens tables, GC-window repair, motif avoidance, CHI tRNA-strain index, TASEP ribosome-flow KMC simulation, FBA constraint export |
| prime_design | pegRNA design (PBS 10-17 nt by Tm, RTT 10-20 nt), PE2/PE3 nicking sgRNA finder, outcome distribution, off-target scan |
| deepsplice | donor (9 nt) / acceptor (15 nt) PWM log-odds scoring, variant delta, isoform consequence calls |
| str_scope | tandem-repeat detection 1-6 bp units, expansion classification, diagnostic potential index |
| rna_decoder | DRACH/m6A site prediction with regional priors + exposure proxy, modification map, mRNA optimization proposals |
| promoter_lib | sigma70 promoter scoring (-35/-10/spacer/UP element), strength-targeted design, library generation, motif heatmap |
| dark_genome | TF motif scan (IUPAC), enhancer clustering, CpG islands, lncRNA candidates, hypothesis generation |
| virtual_cell | stoichiometric FBA (scipy linprog/HiGHS), gene knockout lethality + flux rerouting, dynamic FBA growth simulation |
| synbio_studio | Hill-kinetics ODE circuit simulation (solve_ivp), toggle switch bistability, repressilator, truth-table verification |
| living_computer | boolean expression -> circuit compiler with fidelity scoring, parts registry, stochastic noise analysis (CV) |
| omega_stats | metric recording, per-metric aggregates, sub-network rollup |
| ecosystem | SDK snippet generation, plugin manifest contract, machine-readable API reference |
| dna_to_code | 6 biology->Python concept translations with executable analogies |

### Known limits (named, not hidden)

- External database integrations (PubMed, NCBI, UniProt, ClinVar, AlphaFold) are
  not yet wired; modules that need them use built-in reference data or physics/
  statistics models. Live connectors are a later drop.
- No trained deep models yet (GenomeGPT, DeepSplice-full, BioImage AI etc. need
  learned weights); current versions use PWM/ODE/FBA/heuristic models that are
  real computations, not labels.
- Frontend/UI is API-only in this drop.
- CRISPR on/off-target scores are calibrated heuristics (Doench-style), not the
  published Rule Set 2 / CFD weight matrices.

## Quickstart

```bash
pip install -e .[dev]
python -m pytest -q                 # 51 tests
python - <<'PY'
from omega.search import biological_search
print(biological_search("CRISPR guide design")["results"][0]["name"])
from sugarcode.modules.crispr_opt import design_guides
print(design_guides("ATG" + "CG"*40 + "GG" + "A"*40)["guides"][0])
PY
uvicorn omega.api:app --reload      # API surface
```

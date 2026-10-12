> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# ChemGPT Engine

ChemGPT Engine: A multi-parameter molecular optimization engine that generates novel chemical compounds with optimized ADMET profiles. It predicts critical properties like LogP and solubility while providing retrosynthetic pathways. ChemGPT balances therapeutic potential with synthetic feasibility, enabling the rapid discovery of small molecules tailored to specific biological targets and safety profiles. ChemGPT Engine can be elevated into a generative–predictive molecular design system that operates across the full chemical–biological stack, integrating transformer-based molecular language models with physics-informed scoring and synthesis-aware constraints. Instead of treating molecules as static SMILES strings, the engine would learn joint representations across graph structures, 3D conformers, and quantum-derived descriptors, enabling it to reason simultaneously about topology, stereochemistry, and electronic properties. A diffusion-based generative backbone—conditioned on target binding pockets, pharmacophore constraints, and ADMET priors—could iteratively sample chemically valid structures while optimizing along multiple objectives such as lipophilicity (LogP), aqueous solubility, permeability, and metabolic stability. These objectives would not be heuristically balanced but embedded into a Pareto optimization framework, allowing ChemGPT to explore trade-offs between potency, toxicity, and synthesizability in a controlled, interpretable manner.

At the property prediction layer, ChemGPT would integrate hybrid models combining graph neural networks (GNNs), equivariant neural networks (for 3D spatial reasoning), and quantum-informed surrogate models to approximate DFT-level calculations in milliseconds. This allows real-time estimation of binding affinity, partial charges, HOMO–LUMO gaps, and reactivity indices, which are critical for both drug efficacy and stability. ADMET prediction would be enhanced through multi-task learning on curated pharmacokinetic datasets, incorporating transporter interactions (e.g., P-gp), CYP450 metabolism predictions, and toxicity endpoints such as hERG inhibition or hepatotoxicity. Crucially, uncertainty quantification (via Bayesian neural networks or ensemble methods) would be built into every prediction, enabling researchers to distinguish between high-confidence candidates and speculative designs.
A key differentiator would be ChemGPT’s tight coupling with structural biology and docking pipelines. Generated molecules would be automatically conformer-optimized and docked into target protein structures (experimentally resolved or predicted via systems like AlphaFold), using differentiable docking or learned scoring functions to refine binding poses. Feedback from docking—binding energy landscapes, interaction fingerprints, hydrogen bonding networks—would be looped back into the generative model as reinforcement signals, creating a closed optimization cycle. Beyond static docking, the engine could interface with accelerated molecular dynamics simulations to assess binding stability over time, capturing entropic effects and induced fit phenomena that are often missed in traditional pipelines.
On the synthesis side, ChemGPT would move beyond simple retrosynthetic suggestions to full synthesis planning under real-world constraints. Leveraging transformer-based retrosynthesis models trained on reaction datasets (e.g., USPTO), the system could generate multi-step synthetic routes optimized for yield, cost, and reagent availability. It would incorporate reaction condition prediction (solvents, catalysts, temperature) and evaluate route feasibility using cheminformatics rules and learned reaction success probabilities. Integration with automated lab platforms or electronic lab notebooks would allow ChemGPT to output executable protocols, bridging the gap between in silico design and wet-lab realization.
Ultimately, ChemGPT Engine could evolve into a self-improving chemical discovery system by incorporating active learning loops from experimental feedback. Data from high-throughput screening, failed syntheses, or unexpected toxicity results would be reintegrated into the training pipeline, refining both generative and predictive components. Over time, this creates a system that not only designs molecules but learns the underlying principles of medicinal chemistry in a dynamic, data-driven way—adapting to new targets, chemical spaces, and therapeutic challenges while continuously improving its ability to generate viable, synthesizable, and clinically relevant compounds.

## Whole-claim corrections (2026-10-12)

These corrections apply to the original wording above. They describe the
implementation at commit 99cb2d329690cf946ae491cb3ca027ee66b7f656 and do not
claim that the aspirational capability has been implemented.

- S5-069.03.C07, original claim: "synthesizable".
  Corrected scope (OVERSTATED): Synthetic accessibility is a fragment score without empirical fitting; route templates do not establish synthesizability.


## STACK-B3 row-specific scope corrections

These descriptions supersede the named current-capability claims only. They do
not implement an aspirational model or establish a chemistry, therapeutic or
clinical outcome. The original banner and source text remain unchanged.

### S5-006.A01

Decision: CORRECT. Current label: PARTIAL.

Samples and joins entries from a fixed fragment dictionary into subset SMILES strings; no claim of new-compound identity or chemical suitability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,147-173`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-006.A02.C01

Decision: CORRECT. Current label: PARTIAL.

LogP is the rounded sum of hand-set fragment contributions; other returned descriptors are fragment counts or arithmetic proxies, not property predictions.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-006.A02.C02

Decision: CORRECT. Current label: PARTIAL.

logS is a hand-set arithmetic function of additive LogP and fragment mass; no solubility data fit or assay evidence is included in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-006.A02.C03

Decision: CORRECT. Current label: PARTIAL.

Returns a count of four threshold violations over fragment-additive mass, LogP and donor/acceptor counts; not an absorption outcome.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-006.A02.C04

Decision: CORRECT. Current label: PARTIAL.

Returns fixed fragment-count/LogP-derived CYP and hERG proxies; no endpoint fit, patient outcome or safety conclusion in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:98-126,250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-006.A04

Decision: CORRECT. Current label: PARTIAL.

Assigns fixed reaction-name templates to fragment removals; no reaction search or executable synthesis route.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:176-183,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-020.A01.C01

Decision: CORRECT. Current label: PARTIAL.

The inspected core.py implements fragment sampling and arithmetic; it contains no trained generator invocation. This statement is limited to the inspected module path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-020.A01.C02

Decision: CORRECT. Current label: PARTIAL.

The registry identifier chemgpt_engine is retained for compatibility; it does not describe the model class in the inspected core.py.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-020.A02.C01

Decision: CORRECT. Current label: PARTIAL.

Samples and joins entries from a fixed fragment dictionary into subset SMILES strings; no claim of new-compound identity or chemical suitability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,147-173`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-020.A02.C02

Decision: CORRECT. Current label: PARTIAL.

LogP is the rounded sum of hand-set fragment contributions; other returned descriptors are fragment counts or arithmetic proxies, not property predictions.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-020.A04

Decision: CORRECT. Current label: PARTIAL.

The inspected core.py implements fragment sampling and arithmetic; it contains no trained generator invocation. This statement is limited to the inspected module path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.01.C01

Decision: CORRECT. Current label: PARTIAL.

Generates samples from a fixed fragment dictionary; no novelty, discovery speed or chemical identity result is established by sampling.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,147-173`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.01.C02

Decision: CORRECT. Current label: PARTIAL.

Ranks hand-set ADMET proxies over sampled fragment compositions; ranking is not evidence of improved pharmacokinetic outcomes.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-173,250-254,296-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.02.C01

Decision: CORRECT. Current label: PARTIAL.

LogP is the rounded sum of hand-set fragment contributions; other returned descriptors are fragment counts or arithmetic proxies, not property predictions.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.02.C02

Decision: CORRECT. Current label: PARTIAL.

logS is a hand-set arithmetic function of additive LogP and fragment mass; no solubility data fit or assay evidence is included in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.02.C03

Decision: CORRECT. Current label: PARTIAL.

Assigns fixed reaction-name templates to fragment removals; no reaction search or executable synthesis route.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:176-183,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.03.C01

Decision: CORRECT. Current label: UNSUPPORTED.

No therapeutic or clinical outcome is supported by the inspected fragment-proxy module; output is a computational candidate worksheet.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126,307-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-065.03.C02

Decision: CORRECT. Current label: PARTIAL.

Synthetic accessibility is a hand-set fragment score; reaction templates do not establish synthesis success, practical feasibility or viability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:117,176-183,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.03.C03

Decision: CORRECT. Current label: PARTIAL.

Generates samples from a fixed fragment dictionary; no novelty, discovery speed or chemical identity result is established by sampling.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,147-173`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.03.C04

Decision: CORRECT. Current label: PARTIAL.

Pocket inputs are donor/acceptor counts, hydrophobicity and volume used in a static arithmetic score; no target sequence/structure or target-specific model is used in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260,296-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.03.C05

Decision: CORRECT. Current label: PARTIAL.

Returns fixed fragment-count/LogP-derived CYP and hERG proxies; no endpoint fit, patient outcome or safety conclusion in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:98-126,250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.04.C01

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-065.04.C02

Decision: CORRECT. Current label: PARTIAL.

Returns composition-linear HOMO/LUMO, gap and related arithmetic proxies; no quantum solver, DFT comparison or quantum-trained model appears in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:245-248`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.04.C03

Decision: CORRECT. Current label: PARTIAL.

Assembly applies fragment membership and fluorine-placement restrictions; route planning assigns fixed conditions and inventory-name membership. These do not establish chemical or lab feasibility.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.05.C01

Decision: CORRECT. Current label: PARTIAL.

Returns atom/edge data from assembled subset SMILES. Parser boundaries are lexical/structural only; no chemical sanitization, chirality or geometry assessment.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:66-95,222-226`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.05.C02

Decision: CORRECT. Current label: PARTIAL.

Creates seeded Gaussian random-walk coordinates, sorts a successive-coordinate strain proxy and normalizes exponential weights; no force-field optimization or bond-geometry constraint solve.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:228-235`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.05.C03

Decision: CORRECT. Current label: PARTIAL.

Returns composition-linear HOMO/LUMO, gap and related arithmetic proxies; no quantum solver, DFT comparison or quantum-trained model appears in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:245-248`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.05.C04

Decision: CORRECT. Current label: PARTIAL.

Returns atom/edge data from assembled subset SMILES. Parser boundaries are lexical/structural only; no chemical sanitization, chirality or geometry assessment.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:66-95,222-226`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.05.C05

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-065.05.C06

Decision: CORRECT. Current label: PARTIAL.

Returns composition-linear HOMO/LUMO, gap and related arithmetic proxies; no quantum solver, DFT comparison or quantum-trained model appears in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:245-248`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.06.C01

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-065.06.C02

Decision: CORRECT. Current label: PARTIAL.

Pocket inputs are donor/acceptor counts, hydrophobicity and volume used in a static arithmetic score; no target sequence/structure or target-specific model is used in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260,296-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.06.C03

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-065.06.C04

Decision: CORRECT. Current label: PARTIAL.

Ranks hand-set ADMET proxies over sampled fragment compositions; ranking is not evidence of improved pharmacokinetic outcomes.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-173,250-254,296-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.06.C05

Decision: CORRECT. Current label: PARTIAL.

Subset string assembly and lexical graph parsing do not establish chemical validity; no valence sanitization or stereochemical assessment in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,222-226`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.06.C06

Decision: CORRECT. Current label: PARTIAL.

LogP is the rounded sum of hand-set fragment contributions; other returned descriptors are fragment counts or arithmetic proxies, not property predictions.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.06.C07

Decision: CORRECT. Current label: PARTIAL.

logS is a hand-set arithmetic function of additive LogP and fragment mass; no solubility data fit or assay evidence is included in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.06.C08

Decision: CORRECT. Current label: PARTIAL.

Returns a logistic function of additive LogP divided by a donor-count term; no permeability assay/model fit in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.06.C09

Decision: CORRECT. Current label: PARTIAL.

Returns a clipped arithmetic CYP/rotatable-count proxy; no metabolic dataset or rate model fit in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.07.C01

Decision: CORRECT. Current label: PARTIAL.

Uses nondominated sorting over hand-set objective proxies; conditioned ranking subsequently uses a heuristic penalty and summed score. No removal of heuristic choices is claimed.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:129-173,267-272,296-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.07.C02

Decision: CORRECT. Current label: PARTIAL.

Uses nondominated sorting over hand-set objective proxies; conditioned ranking subsequently uses a heuristic penalty and summed score. No removal of heuristic choices is claimed.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:129-173,267-272,296-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.07.C03

Decision: CORRECT. Current label: PARTIAL.

potency_prior is a fixed donor/acceptor/rotatable-count formula, not a biological potency predictor.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:125,129-136`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.07.C04

Decision: CORRECT. Current label: PARTIAL.

Returns fixed fragment-count/LogP-derived CYP and hERG proxies; no endpoint fit, patient outcome or safety conclusion in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:98-126,250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-065.07.C05

Decision: CORRECT. Current label: PARTIAL.

Synthetic accessibility is a hand-set fragment score; reaction templates do not establish synthesis success, practical feasibility or viability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:117,176-183,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.01.C01

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-066.01.C02

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-066.01.C03

Decision: CORRECT. Current label: PARTIAL.

Returns composition-linear HOMO/LUMO, gap and related arithmetic proxies; no quantum solver, DFT comparison or quantum-trained model appears in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:245-248`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.01.C04

Decision: CORRECT. Current label: PARTIAL.

Returns composition-linear HOMO/LUMO, gap and related arithmetic proxies; no quantum solver, DFT comparison or quantum-trained model appears in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:245-248`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.02.C01

Decision: CORRECT. Current label: PARTIAL.

Returns one static score from fragment counts and pocket summary fields; there is no pose docking or protein-coordinate calculation in this module path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.02.C02

Decision: CORRECT. Current label: PARTIAL.

partial_charge_span is a clipped multiple of a fragment heteroatom-count proxy; no per-atom charges are calculated.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:245-248`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.02.C03

Decision: CORRECT. Current label: PARTIAL.

Computes arithmetic HOMO/LUMO proxy differences and a derived electrophilicity formula; not electronic-structure output.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:245-248`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.02.C04

Decision: CORRECT. Current label: PARTIAL.

Computes arithmetic HOMO/LUMO proxy differences and a derived electrophilicity formula; not electronic-structure output.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:245-248`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.03.C01

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-066.03.C02

Decision: CORRECT. Current label: PARTIAL.

pgp_interaction is a clipped HBA/rotatable-count formula, not a transporter-response model.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.03.C03

Decision: CORRECT. Current label: PARTIAL.

Returns fixed fragment-count/LogP-derived CYP and hERG proxies; no endpoint fit, patient outcome or safety conclusion in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:98-126,250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.03.C04

Decision: CORRECT. Current label: PARTIAL.

Returns fixed fragment-count/LogP-derived CYP and hERG proxies; no endpoint fit, patient outcome or safety conclusion in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:98-126,250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.03.C05

Decision: CORRECT. Current label: PARTIAL.

Returns a clipped arithmetic CYP/hERG/mass-derived proxy; not a liver-toxicity result.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:250-254`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.04.C01

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-066.04.C02

Decision: CORRECT. Current label: PARTIAL.

uncertainty_ensemble draws normal samples around selected proxy outputs using hand-set spread scales; it is not a model ensemble or evidence of confidence coverage for every prediction.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:237-290`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.04.C03

Decision: CORRECT. Current label: PARTIAL.

uncertainty_ensemble draws normal samples around selected proxy outputs using hand-set spread scales; it is not a model ensemble or evidence of confidence coverage for every prediction.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:237-290`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-066.04.C04

Decision: CORRECT. Current label: PARTIAL.

uncertainty_ensemble draws normal samples around selected proxy outputs using hand-set spread scales; it is not a model ensemble or evidence of confidence coverage for every prediction.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:237-290`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.01

Decision: CORRECT. Current label: PARTIAL.

Returns one static score from fragment counts and pocket summary fields; there is no pose docking or protein-coordinate calculation in this module path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.02.C01

Decision: CORRECT. Current label: PARTIAL.

Creates seeded Gaussian random-walk coordinates, sorts a successive-coordinate strain proxy and normalizes exponential weights; no force-field optimization or bond-geometry constraint solve.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:228-235`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.02.C02

Decision: CORRECT. Current label: PARTIAL.

Returns one static score from fragment counts and pocket summary fields; there is no pose docking or protein-coordinate calculation in this module path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.02.C03

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-067.02.C04

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-067.02.C05

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-067.02.C06

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-067.03.C01

Decision: CORRECT. Current label: PARTIAL.

Returns one static score from fragment counts and pocket summary fields; there is no pose docking or protein-coordinate calculation in this module path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.03.C02

Decision: CORRECT. Current label: PARTIAL.

Returns three Boolean flags from scalar proxy thresholds and an integer donor/acceptor count; no atom-resolved interaction network is built.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.03.C03

Decision: CORRECT. Current label: PARTIAL.

Returns three Boolean flags from scalar proxy thresholds and an integer donor/acceptor count; no atom-resolved interaction network is built.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.03.C04

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-067.03.C05

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-067.03.C06

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-067.04.C01

Decision: CORRECT. Current label: PARTIAL.

Returns closed-form retention/off-rate/residence proxies. nanoseconds changes only the reported duration; no time-stepped molecular trajectory is simulated.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:262-265`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.04.C02

Decision: CORRECT. Current label: PARTIAL.

Returns closed-form retention/off-rate/residence proxies. nanoseconds changes only the reported duration; no time-stepped molecular trajectory is simulated.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:262-265`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-067.04.C03

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-067.04.C04

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-068.01.C01

Decision: CORRECT. Current label: PARTIAL.

Returns fixed fragment-removal reaction templates and assigned conditions/yield/cost priors, not a full synthesis planner.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:176-183,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.01.C02

Decision: CORRECT. Current label: PARTIAL.

Assembly applies fragment membership and fluorine-placement restrictions; route planning assigns fixed conditions and inventory-name membership. These do not establish chemical or lab feasibility.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.02.C01

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-068.02.C02

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-068.02.C03

Decision: CORRECT. Current label: PARTIAL.

Assigns fixed reaction-name templates to fragment removals; no reaction search or executable synthesis route.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:176-183,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.02.C04

Decision: CORRECT. Current label: PARTIAL.

Route yield is the product of fixed per-reaction template priors; no reaction outcomes are loaded.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.02.C05

Decision: CORRECT. Current label: PARTIAL.

Route cost uses fixed template prices and a fixed discount on name membership in supplied inventory; no supplier/current-price lookup.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.02.C06

Decision: CORRECT. Current label: PARTIAL.

reagent_available is membership of a fragment name in a caller-supplied set; no inventory connector or external availability check.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.03.C01

Decision: CORRECT. Current label: PARTIAL.

Returns reaction-class default solvent/catalyst labels and temperature bands; no condition prediction or lab execution.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.03.C02

Decision: CORRECT. Current label: PARTIAL.

Assembly applies fragment membership and fluorine-placement restrictions; route planning assigns fixed conditions and inventory-name membership. These do not establish chemical or lab feasibility.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.03.C03

Decision: CORRECT. Current label: PARTIAL.

Assembly applies fragment membership and fluorine-placement restrictions; route planning assigns fixed conditions and inventory-name membership. These do not establish chemical or lab feasibility.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-068.03.C04

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-068.04.C01

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-068.04.C02

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-068.04.C03

Decision: CORRECT. Current label: UNSUPPORTED.

The named capability/data integration is not implemented in the inspected core.py. Current outputs are fragment/proxy dictionaries and fixed route templates, not that capability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-95,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-069.01.C01

Decision: CORRECT. Current label: PARTIAL.

active_learning_update is a standalone normal-precision update over scalar observations; it does not update the fragment generator or predictive components in the inspected core.py.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:292-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.01.C02

Decision: CORRECT. Current label: PARTIAL.

active_learning_update is a standalone normal-precision update over scalar observations; it does not update the fragment generator or predictive components in the inspected core.py.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:292-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.01.C03

Decision: CORRECT. Current label: PARTIAL.

Accepts caller-supplied scalar observations without assay schemas, outcome ingestion or model integration; no external experimental feedback loop in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:292-294`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.02.C01

Decision: CORRECT. Current label: PARTIAL.

Accepts caller-supplied scalar observations without assay schemas, outcome ingestion or model integration; no external experimental feedback loop in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:292-294`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.02.C02

Decision: CORRECT. Current label: PARTIAL.

Accepts caller-supplied scalar observations without assay schemas, outcome ingestion or model integration; no external experimental feedback loop in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:292-294`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.02.C03

Decision: CORRECT. Current label: PARTIAL.

Accepts caller-supplied scalar observations without assay schemas, outcome ingestion or model integration; no external experimental feedback loop in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:292-294`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.02.C04

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-069.02.C05

Decision: CORRECT. Current label: UNSUPPORTED.

The named learned-model or training mechanism is not present in the inspected core.py. Its current alternative is fixed fragment sampling, arithmetic ranking and standalone statistics.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:147-173,217-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-069.03.C01

Decision: CORRECT. Current label: PARTIAL.

Samples and joins entries from a fixed fragment dictionary into subset SMILES strings; no claim of new-compound identity or chemical suitability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:35-63,147-173`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.03.C02

Decision: CORRECT. Current label: UNSUPPORTED.

No learned medicinal-chemistry principles are supported in the inspected core.py; fragment dictionary constants and fixed formulas are used.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:6-28,98-173,245-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-069.03.C03

Decision: CORRECT. Current label: PARTIAL.

Pocket inputs are donor/acceptor counts, hydrophobicity and volume used in a static arithmetic score; no target sequence/structure or target-specific model is used in this path.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:256-260,296-300`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.03.C04

Decision: CORRECT. Current label: PARTIAL.

Samples the fixed fragment dictionary only; no general chemical-space coverage claim.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:6-28,147-173`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.03.C05

Decision: CORRECT. Current label: UNSUPPORTED.

No therapeutic or clinical outcome is supported by the inspected fragment-proxy module; output is a computational candidate worksheet.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126,307-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-069.03.C06

Decision: CORRECT. Current label: PARTIAL.

Synthetic accessibility is a hand-set fragment score; reaction templates do not establish synthesis success, practical feasibility or viability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:117,176-183,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.03.C07

Decision: CORRECT. Current label: PARTIAL.

Synthetic accessibility is a hand-set fragment score; reaction templates do not establish synthesis success, practical feasibility or viability.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:117,176-183,274-278`.

CORRECT narrows the claim to inspected behavior; original broader claim stays PARTIAL, not COMPLETE.

### S5-069.03.C08

Decision: CORRECT. Current label: UNSUPPORTED.

No therapeutic or clinical outcome is supported by the inspected fragment-proxy module; output is a computational candidate worksheet.

Source: `692143ee:src/sugarcode/modules/chemgpt_engine/core.py:102-126,307-308`.

Named capability is unsupported in the inspected file; corrected description does not implement it.

### S5-DISC-chemgpt_engine

Decision: CORRECT. Current label: PARTIAL.

Keep the original banner unchanged. This row-specific correction describes only the inspected chemgpt_engine/core.py: fragment sampling and arithmetic proxies, not the other model families listed in the program-level banner.

Source: `src/sugarcode/modules/chemgpt_engine/core.py:1-333`.

Program-level banner is not changed and is not evidence that this module implements every listed model family.

### S5-H17-3

Decision: CORRECT. Current label: PARTIAL.

The historical ordering and timestamps are retained as reported history; this run does not establish source-edit chronology from them.

Source: `CONTRACT_H17.md:3; tests/test_h17_chemgpt_mass_contract.py:18-87`.

Historical provenance remains bounded; current local test execution does not authenticate the original external oracle or chronology.

### S5-H17-5

Decision: CORRECT. Current label: PARTIAL.

Two vendored frozen JSON files are hash-pinned by the test. Producer runtime, original archive and oracle-generation provenance were not established in this inspection; no fresh RDKit oracle was run.

Source: `CONTRACT_H17.md:5; tests/test_h17_chemgpt_mass_contract.py:18-87`.

Historical provenance remains bounded; current local test execution does not authenticate the original external oracle or chronology.

### S5-H17-6

Decision: CORRECT. Current label: PARTIAL.

Frozen data contains 156 inputs, 8 refusals and 148 returned cases. Tests check the frozen sanitation flags and arithmetic mass tolerance; this is not a fresh chemical sanitation run.

Source: `CONTRACT_H17.md:6; tests/test_h17_chemgpt_mass_contract.py:18-87`.

Historical provenance remains bounded; current local test execution does not authenticate the original external oracle or chronology.

### S5-H17-15

Decision: CORRECT. Current label: PARTIAL.

Frozen historical failures compare rounded public mass to reference mass. Current tests separately check raw arithmetic and frozen display regression; this does not establish a broader oracle defect or external provenance.

Source: `CONTRACT_H17.md:15; tests/test_h17_chemgpt_mass_contract.py:18-87`.

Historical provenance remains bounded; current local test execution does not authenticate the original external oracle or chronology.

### S5-H17-19

Decision: CORRECT. Current label: PARTIAL.

The historical NOT RUN receipt remains historical. This patch run executed the seven H17 tests without fresh RDKit or network access; it does not rewrite the earlier receipt.

Source: `CONTRACT_H17.md:19; tests/test_h17_chemgpt_mass_contract.py:18-87`.

Historical provenance remains bounded; current local test execution does not authenticate the original external oracle or chronology.

### S5-CODEDOC-052.C03

Decision: BUILD. Current label: PARTIAL.

Bounded lexical subset parser refuses charge syntax and all unsupported tokens before graph construction; no chemical sanitization or valence assessment. The listed state guards do not close general SMILES grammar: C((C)) and C(=1CC1) still accept.

Source: `src/sugarcode/modules/chemgpt_engine/core.py:66-120`.

Local code boundary changed and tested; independent reproduction fields are intentionally empty, so final label remains PARTIAL.

### S5-CODEDOC-053

Decision: CORRECT. Current label: PARTIAL.

Returns fragment-additive property and endpoint proxies from fixed tables/formulas; no ADMET dataset fit or assay-backed profile in the inspected function.

Source: `src/sugarcode/modules/chemgpt_engine/core.py:127-151`.

CORRECT scopes the profile description; no property-model implementation change is claimed.

### S5-CODEDOC-056.C01

Decision: CORRECT. Current label: PARTIAL.

Optional ChEMBL similarity lookup returns source-reported neighbors, filters approved_neighbors by max_phase == 4 and emits a threshold-based similarity label; no market-status or chemical/patent novelty conclusion.

Source: `src/sugarcode/modules/chemgpt_engine/core.py:211-240`.

At this pin the approval-phase predicate is already ==4. No live provider request or novelty proof in this run; claim is narrowed.

"""Export-level forwarding and refusal contract; core arithmetic is not exercised."""
import importlib
import inspect
import re
import sys
import numpy as np
import pytest

CASES = [
    ('sugarcode.llm.seed_checked_router', 'sugarcode.llm.router', 'train_softmax'),
    ('sugarcode.modules.bio_copilot.seed_checked', 'sugarcode.modules.bio_copilot.core', 'propagate_uncertainty'),
    ('sugarcode.modules.bio_switch.seed_checked', 'sugarcode.modules.bio_switch.core', 'gillespie_sensor_noise'),
    ('sugarcode.modules.bioplayground.seed_checked', 'sugarcode.modules.bioplayground.core', 'run_sandbox'),
    ('sugarcode.modules.bioplayground.seed_checked', 'sugarcode.modules.bioplayground.core', 'directed_evolution'),
    ('sugarcode.modules.bioprint_pro.seed_checked', 'sugarcode.modules.bioprint_pro.core', 'oldroyd_b_extrusion'),
    ('sugarcode.modules.bioprint_pro.seed_checked', 'sugarcode.modules.bioprint_pro.core', 'optimize_print'),
    ('sugarcode.modules.biosimvr.seed_checked', 'sugarcode.modules.biosimvr.core', 'simulate_protocol'),
    ('sugarcode.modules.biosimvr.seed_checked', 'sugarcode.modules.biosimvr.core', 'molecular_docking_experiment'),
    ('sugarcode.modules.biosimvr.seed_checked', 'sugarcode.modules.biosimvr.core', 'run_experiment'),
    ('sugarcode.modules.cellfatenet.seed_checked', 'sugarcode.modules.cellfatenet.core', 'identify_attractors'),
    ('sugarcode.modules.cellfatenet.seed_checked', 'sugarcode.modules.cellfatenet.core', 'stochastic_validate'),
    ('sugarcode.modules.cellfatenet.seed_checked', 'sugarcode.modules.cellfatenet.core', 'simulate_fate'),
    ('sugarcode.modules.cellpainter_4d.seed_checked', 'sugarcode.modules.cellpainter_4d.core', 'simulate_population_4d'),
    ('sugarcode.modules.chemgpt_engine.seed_checked', 'sugarcode.modules.chemgpt_engine.core', 'conformer_ensemble'),
    ('sugarcode.modules.chemgpt_engine.seed_checked', 'sugarcode.modules.chemgpt_engine.core', 'uncertainty_ensemble'),
    ('sugarcode.modules.codon_opt.seed_checked', 'sugarcode.modules.codon_opt.core', 'evolutionary_robustness'),
    ('sugarcode.modules.crispr_muse.seed_checked', 'sugarcode.modules.crispr_muse.core', 'delivery_efficiency'),
    ('sugarcode.modules.crispr_muse.seed_checked', 'sugarcode.modules.crispr_muse.core', 'simulate_digital_lab'),
    ('sugarcode.modules.dark_genome.seed_checked', 'sugarcode.modules.dark_genome.core', 'variant_counterfactual'),
    ('sugarcode.modules.docking_studio.seed_checked', 'sugarcode.modules.docking_studio.core', 'monte_carlo_dock'),
    ('sugarcode.modules.docking_studio.seed_checked_vina', 'sugarcode.modules.docking_studio.vina_real', 'prepare_ligand_from_smiles'),
    ('sugarcode.modules.docking_studio.seed_checked_vina', 'sugarcode.modules.docking_studio.vina_real', 'dock'),
    ('sugarcode.modules.dti_bench.seed_checked', 'sugarcode.modules.dti_bench.core', 'validate_dti'),
    ('sugarcode.modules.evofold_4d.seed_checked', 'sugarcode.modules.evofold_4d.core', 'langevin_dynamics'),
    ('sugarcode.modules.evofold_4d.seed_checked', 'sugarcode.modules.evofold_4d.core', 'dynamics_report'),
    ('sugarcode.modules.genomegpt.seed_checked', 'sugarcode.modules.genomegpt.core', 'masked_sequence_objective'),
    ('sugarcode.modules.liquid_biopsy.seed_checked', 'sugarcode.modules.liquid_biopsy.core', 'bootstrap_haplotype_weights'),
    ('sugarcode.modules.liquid_biopsy.seed_checked', 'sugarcode.modules.liquid_biopsy.core', 'fragment_length_model'),
    ('sugarcode.modules.living_computer.seed_checked', 'sugarcode.modules.living_computer.core', 'stochastic_simulate'),
    ('sugarcode.modules.living_computer.seed_checked', 'sugarcode.modules.living_computer.core', 'monte_carlo_robustness'),
    ('sugarcode.modules.neohunter.seed_checked', 'sugarcode.modules.neohunter.core', 'neoantigen_pipeline'),
    ('sugarcode.modules.neuro_pipeline.seed_checked', 'sugarcode.modules.neuro_pipeline.core', 'synthetic_promoter_dataset'),
    ('sugarcode.modules.neuro_pipeline.seed_checked', 'sugarcode.modules.neuro_pipeline.core', 'sequence_pipeline_demo'),
    ('sugarcode.modules.neuro_pipeline.seed_checked', 'sugarcode.modules.neuro_pipeline.core', 'train_on_sequences'),
    ('sugarcode.modules.phage_tx.seed_checked', 'sugarcode.modules.phage_tx.core', 'evolve_cocktail'),
    ('sugarcode.modules.protein_painter.seed_checked', 'sugarcode.modules.protein_painter.core', 'engineering_blueprint'),
    ('sugarcode.modules.protein_painter.seed_checked', 'sugarcode.modules.protein_painter.core', 'painter_diagnostics'),
    ('sugarcode.modules.riboswitch.seed_checked', 'sugarcode.modules.riboswitch.core', 'optimize_switch'),
    ('sugarcode.modules.synbio_wizard.seed_checked', 'sugarcode.modules.synbio_wizard.core', 'compile_project'),
    ('sugarcode.modules.synbio_wizard.seed_checked', 'sugarcode.modules.synbio_wizard.core', 'run_wizard'),
    ('sugarcode.modules.syndroid.seed_checked', 'sugarcode.modules.syndroid.core', 'stochastic_gene_expression'),
    ('sugarcode.modules.syndroid.seed_checked', 'sugarcode.modules.syndroid.core', 'evolutionary_stability'),
    ('sugarcode.modules.synlife_evo.seed_checked', 'sugarcode.modules.synlife_evo.core', 'optimize_stability'),
    ('sugarcode.modules.synthetic_life.seed_checked', 'sugarcode.modules.synthetic_life.core', 'compile_synthetic_life'),
    ('sugarcode.modules.vector_opt.seed_checked', 'sugarcode.modules.vector_opt.core', 'directed_evolution'),
    ('sugarcode.modules.stability_ai.seed_guard', 'sugarcode.modules.stability_ai.core', 'analyze_stability'),
    ('sugarcode.modules.stability_ai.seed_guard', 'sugarcode.modules.stability_ai.core', 'analyze_stability_v2'),
    ('sugarcode.modules.syndroid.seed_guard', 'sugarcode.modules.syndroid.core', 'mechanistic_cell_program'),
    ('sugarcode.modules.syndroid.seed_guard', 'sugarcode.modules.syndroid.core', 'design_syndroid'),
]
CAP = 2**63-1
TO_RESTORE = []

@pytest.fixture(autouse=True)
def restore_exports(monkeypatch):
    yield
    monkeypatch.undo()
    for module, original, package, package_state in reversed(TO_RESTORE):
        if original is None:sys.modules.pop(module, None)
        else:sys.modules[module] = original
        package.__dict__.clear()
        package.__dict__.update(package_state)
    TO_RESTORE.clear()

class Marker:
    def __init__(self,name):self.name=name

def setup_spy(monkeypatch,module,coremodule,name):
    core=importlib.import_module(coremodule)
    original=getattr(core,name)
    sig=inspect.signature(original)
    calls=[]
    def spy(*args,**kwargs):
        b=sig.bind(*args,**kwargs)
        calls.append(dict(b.arguments))
        b.apply_defaults()
        return dict(b.arguments)
    spy.__signature__=sig
    spy.__name__=name
    monkeypatch.setattr(core,name,spy)
    original_module = sys.modules.get(module)
    package = importlib.import_module(module.rsplit('.', 1)[0])
    package_state = dict(vars(package))
    sys.modules.pop(module,None)
    wrapped=importlib.import_module(module)
    TO_RESTORE.append((module, original_module, package, package_state))
    return getattr(wrapped,name),sig,calls,spy

def inputs(sig,seed,style):
    values={n:(seed if n=='seed' else Marker(n)) for n in sig.parameters}
    positional=[n for n,p in sig.parameters.items() if p.kind in (p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD)]
    if style=='keyword':take=0
    elif style=='positional':take=len(positional)
    else:take=max(1,len(positional)//2) if positional else 0
    pos=positional[:take]
    return [values[n] for n in pos],{n:v for n,v in values.items() if n not in pos},values

@pytest.mark.parametrize('module,coremodule,name',CASES)
@pytest.mark.parametrize('style',['keyword','positional','mixed'])
@pytest.mark.parametrize('raw',[0,7,CAP,np.int64(7),np.uint64(CAP)])
def test_export_forwards_every_parameter_unchanged(monkeypatch,module,coremodule,name,style,raw):
    fn,sig,calls,spy=setup_spy(monkeypatch,module,coremodule,name)
    args,kw,values=inputs(sig,raw,style)
    result=fn(*args,**kw)
    assert len(calls)==1 and set(calls[0])==set(sig.parameters)
    for key,value in values.items():
        if key=='seed':assert type(result[key]) is int and result[key]==int(raw)
        else:assert result[key] is value,key
    assert fn.__wrapped__ is spy
    assert inspect.signature(fn)==sig

@pytest.mark.parametrize('module,coremodule,name',CASES)
@pytest.mark.parametrize('bad,error,message',[
 (None,TypeError,'seed must be an integer'),(True,TypeError,'seed must be an integer'),
 (np.bool_(False),TypeError,'seed must be an integer'),(1.0,TypeError,'seed must be an integer'),
 ('7',TypeError,'seed must be an integer'),([[]],TypeError,'seed must be an integer'),
 (-1,ValueError,'seed must be between 0 and 9223372036854775807'),
 (CAP+1,ValueError,'seed must be between 0 and 9223372036854775807')])
def test_export_refuses_before_core(monkeypatch,module,coremodule,name,bad,error,message):
    fn,sig,calls,_=setup_spy(monkeypatch,module,coremodule,name)
    args,kw,_=inputs(sig,bad,'mixed')
    with pytest.raises(error,match='^'+re.escape(message)+'$'):fn(*args,**kw)
    assert calls==[]

@pytest.mark.parametrize('module,coremodule,name',CASES)
def test_omitted_defaults_are_core_defaults_not_injected(monkeypatch,module,coremodule,name):
    fn,sig,calls,_=setup_spy(monkeypatch,module,coremodule,name)
    required={n:Marker(n) for n,p in sig.parameters.items() if p.default is inspect.Parameter.empty}
    result=fn(**required)
    assert calls==[required]
    for n,p in sig.parameters.items():
        if n in required:assert result[n] is required[n]
        else:assert result[n] is p.default or result[n]==p.default
    assert type(result['seed']) is int

import math
import pytest
from sugarcode.modules.biogpt_lit import *

def graph():
 k=KnowledgeGraph(); k.ingest({'id':'p1','year':2018,'citations':30,'replicated':True,'rigor':.8,'claims':[{'subject':'A','relation':'activates','object':'B','n':80,'condition':'cell1'},{'subject':'B','relation':'inhibits','object':'C','n':80}]}); k.ingest({'id':'p2','year':2022,'citations':5,'rigor':.5,'claims':[{'subject':'A','relation':'inhibits','object':'B','n':20,'condition':'cell2'}]}); return k

def test_legacy_query_contradiction_and_multihop():
 k=graph(); assert k.query('A','B')['consensus'] and k.contradictions() and k.multi_hop('A','C')['connected']

def test_claim_extractor_precision():
 r=extract_claims('TP53 activates BAX. random words here.'); assert r==[{'subject':'TP53','relation':'activates','object':'BAX'}]

def test_full_text_parses_methods_and_assets():
 r=parse_full_text({'title':'TP53 activates BAX','methods':'randomized blinded replication n=20','figures':[1],'supplements':[1,2]}); assert r['claims'] and r['methods']['has_randomization'] and r['methods']['has_blinding'] and r['figure_count']==1 and r['supplement_count']==2

def test_evidence_quality_rewards_replication():
 a=evidence_quality({'citations':1,'replicated':False,'rigor':.4},{'n':10}); b=evidence_quality({'citations':100,'replicated':True,'rigor':.8,'preregistered':True},{'n':100}); assert b['strength']>a['strength'] and a['preliminary']

def test_temporal_consensus_tracks_years():
 r=temporal_consensus(graph(),'A','B'); assert [x['year'] for x in r['trajectory']]==[2018,2022] and r['trajectory'][0]['consensus']=='activates'

def test_contradiction_context_preserves_conditions():
 r=contradiction_context(graph(),'A','B'); assert r['count']==1 and set(r['conflicts'][0]['contexts'])=={'activates','inhibits'} and r['conflicts'][0]['resolution_experiment']

def test_evidence_paths_include_provenance():
 r=evidence_paths(graph(),'A','C'); assert r['connected'] and r['paths'][0]['support'][0]['papers'] and r['paths'][0]['path_strength']>0

def test_meta_analysis_weighted_and_uncertain():
 r=meta_analysis([.2,.3,.4],[.1,.1,.2]); assert .2<r['random_effect']<.4 and r['ci95'][0]<r['random_effect']<r['ci95'][1]

def test_gaps_prioritize_contradictions():
 r=prioritize_gaps(graph()); assert r[0]['information_leverage']>=r[-1]['information_leverage'] and any(x['contradiction'] for x in r)

def test_hypothesis_is_structured_nonprocedural():
 r=structured_hypothesis(graph(),'A'); assert r['hypotheses'] and r['hypotheses'][0]['predicted_outcomes'] and r['hypotheses'][0]['controls'] and r['hypotheses'][0]['status'].startswith('non-procedural')

def test_validation_feedback_updates_graph():
 k=graph(); before=len(k.claims); r=update_validation(k,'A','activates','B',True); assert len(k.claims)==before+1 and r['after']['confidence']>=r['before']['confidence']

def test_diagnostics_honest_finite():
 d=graph_diagnostics(graph()); assert len(d)==14 and all(math.isfinite(v) for v in d.values())

def test_report_complete_honest_auditable():
 r=literature_reasoning_report(graph(),'A','A','C'); assert r['hypotheses'] and r['contradictions'] and r['evidence_paths']['connected'] and r['diagnostics'] and 'no trained transformer/GNN' in r['model_status'] and 'paper IDs' in r['audit_note']

def test_invalid_meta_analysis_rejected():
 with pytest.raises(ValueError): meta_analysis([1],[0])


def test_extract_claims_skips_negated_and_loss_of_function_sentences():
    assert extract_claims('Neither drug inhibits EGFR.') == []
    assert extract_claims('Loss of PTEN activates AKT. PTEN knockdown activates AKT.') == []
    assert extract_claims('We found no evidence that IL6 activates STAT3.') == []
    assert extract_claims('Metformin does not inhibit mTOR; AMPK inhibits mTOR.') == [
        {'subject': 'AMPK', 'relation': 'inhibits', 'object': 'mTOR'}]

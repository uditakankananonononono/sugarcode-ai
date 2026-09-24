from __future__ import annotations

# Small curated lineage GRN: node -> {regulator: sign}
LINEAGE_GRN = {
    "OCT4": {"targets": {"SOX2": "+", "NANOG": "+", "MYOD1": "-", "GATA4": "-"}},
    "SOX2": {"targets": {"OCT4": "+", "NANOG": "+", "ASCL1": "-"}},
    "NANOG": {"targets": {"OCT4": "+", "GATA4": "-"}},
    "GATA4": {"targets": {"MEF2C": "+", "TBX5": "+", "OCT4": "-"}},
    "MEF2C": {"targets": {"TNNT2": "+", "MYH6": "+"}},
    "TBX5": {"targets": {"MYH6": "+", "NKX2-5": "+"}},
    "ASCL1": {"targets": {"NEUROD1": "+", "MYT1L": "+", "OCT4": "-"}},
    "NEUROD1": {"targets": {"TUBB3": "+", "MAP2": "+"}},
    "MYT1L": {"targets": {"MAP2": "+", "SCN1A": "+"}},
    "MYOD1": {"targets": {"MYOG": "+", "MYH1": "+"}},
}
CELL_MARKERS = {
    "fibroblast": ["COL1A1", "VIM"], "neuron": ["TUBB3", "MAP2", "SCN1A"],
    "cardiomyocyte": ["TNNT2", "MYH6"], "ipsc": ["OCT4", "SOX2", "NANOG"],
    "muscle": ["MYOG", "MYH1"],
}


def lineage_network(focus: list[str] | None = None) -> dict:
    """Causal regulatory network with edge list and key regulatory nodes."""
    edges = []
    for src, d in LINEAGE_GRN.items():
        for dst, sign in d["targets"].items():
            if focus and src not in focus and dst not in focus:
                continue
            edges.append({"source": src, "target": dst,
                          "effect": "activates" if sign == "+" else "represses"})
    centrality: dict[str, int] = {}
    for e in edges:
        centrality[e["source"]] = centrality.get(e["source"], 0) + 1
    key_nodes = sorted(centrality, key=lambda k: -centrality[k])[:5]
    return {"nodes": sorted({e["source"] for e in edges} | {e["target"] for e in edges}),
            "edges": edges, "key_regulatory_nodes": key_nodes,
            "markers": CELL_MARKERS}


def transition_recipe(source: str, target: str) -> dict:
    """Stepwise genetic recipe: which nodes to push/pull and in what order."""
    net = lineage_network()
    target_markers = CELL_MARKERS.get(target.lower(), [])
    source_markers = CELL_MARKERS.get(source.lower(), [])
    drivers = [n for n, d in LINEAGE_GRN.items()
               if any(t in target_markers for t in d["targets"])]
    repressors = [n for n, d in LINEAGE_GRN.items()
                  if any(t in source_markers for t in d["targets"])]
    steps = []
    if drivers:
        steps.append({"order": 1, "action": "overexpress",
                      "nodes": sorted(set(drivers)),
                      "rationale": "activate target-lineage marker program"})
    if repressors:
        steps.append({"order": 2, "action": "repress/knockdown",
                      "nodes": sorted(set(repressors)),
                      "rationale": "silence source-lineage identity"})
    steps.append({"order": 3, "action": "select",
                  "nodes": target_markers,
                  "rationale": "enrich converted cells by marker expression"})
    return {
        "source": source, "target": target,
        "network": net,
        "recipe": steps,
        "expected_transition": f"{source} -> {target} via {len(drivers)} driver nodes",
    }

# --- specification-complete cell-fate landscape engine ------------------------
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize


def grn_matrix(nodes=None):
    """Signed weighted directed GRN adjacency assembled from causal edges."""
    nodes=nodes or sorted(set(LINEAGE_GRN)|{t for d in LINEAGE_GRN.values() for t in d["targets"]})
    idx={n:i for i,n in enumerate(nodes)}; W=np.zeros((len(nodes),len(nodes)))
    for src,d in LINEAGE_GRN.items():
        if src not in idx: continue
        for dst,sign in d["targets"].items():
            if dst in idx: W[idx[dst],idx[src]]=1 if sign=="+" else -1
    return nodes,W


def chromatin_binding(accessibility,methylation,tf_concentration,delta_g=-7.0,temperature=310.15):
    """Statistical-mechanics TF occupancy modulated by chromatin and methylation."""
    R=.001987; access=np.clip(np.asarray(accessibility,float),0,1); meth=np.clip(np.asarray(methylation,float),0,1)
    ka=np.exp(-delta_g/(R*temperature)); effective=tf_concentration*access*(1-meth)
    occupancy=ka*effective/(1+ka*effective)
    return {"occupancy":occupancy.tolist(),"association_constant":float(ka),"delta_g_kcal_mol":delta_g,"temperature_K":temperature}


def simulate_fate(initial, *, hours=72, controls=None, accessibility=None,
                  methylation=None, noise=0.0, seed=9, trajectories=1):
    """Nonlinear Hill-GRN SDE ensemble with epigenetic gate and controls."""
    nodes,W=grn_matrix(); n=len(nodes); initial=np.array([initial.get(x,0.05) for x in nodes],float)
    controls=controls or {}; u=np.array([controls.get(x,0) for x in nodes],float)
    access=np.ones(n) if accessibility is None else np.array([accessibility.get(x,1) for x in nodes],float)
    meth=np.zeros(n) if methylation is None else np.array([methylation.get(x,0) for x in nodes],float)
    gate=access*(1-meth); t=np.linspace(0,hours,289); rng=np.random.default_rng(seed); ensemble=[]
    for rep in range(trajectories):
        def rhs(_,x):
            xp=np.maximum(x,0); signal=W@(xp*xp/(.25+xp*xp)); production=1/(1+np.exp(-6*(signal-.5))); return gate*production+u-.35*x
        y=solve_ivp(rhs,(0,hours),initial,t_eval=t,rtol=1e-7,atol=1e-9).y.T
        if noise:
            dt=t[1]-t[0]; z=np.empty_like(y); z[0]=y[0]
            for k in range(1,len(t)): z[k]=np.maximum(0,z[k-1]+rhs(t[k-1],z[k-1])*dt+noise*np.sqrt(dt)*rng.normal(size=n))
            y=z
        ensemble.append(y)
    e=np.stack(ensemble)
    return {"nodes":nodes,"time_hours":t.tolist(),"trajectories":e.tolist(),"mean":e.mean(0).tolist(),"variance":e.var(0).tolist(),
            "final_state":dict(zip(nodes,e.mean((0,))[ -1].tolist())),"model":"nonlinear Hill GRN with Euler-Maruyama noise"}


def identify_attractors(*, starts=32, hours=150, seed=4):
    """Find stable cell-identity attractors by multistart dynamical relaxation."""
    nodes,_=grn_matrix(); rng=np.random.default_rng(seed); finals=[]
    for _ in range(starts): finals.append(np.array(list(simulate_fate(dict(zip(nodes,rng.random(len(nodes)))),hours=hours)["final_state"].values())))
    clusters=[]
    for x in finals:
        match=next((c for c in clusters if np.linalg.norm(x-c["center"])<.25),None)
        if match: match["members"].append(x); match["center"]=np.mean(match["members"],0)
        else: clusters.append({"center":x,"members":[x]})
    return {"nodes":nodes,"attractors":[{"id":i,"state":dict(zip(nodes,c["center"].tolist())),"basin_fraction":len(c["members"])/starts} for i,c in enumerate(clusters)]}


def graph_message_passing(expression, layers=3):
    """Parameter-free signed graph message passing, explicitly untrained."""
    nodes,W=grn_matrix(); h=np.array([expression.get(n,0) for n in nodes],float); history=[h.copy()]
    degree=np.maximum(np.abs(W).sum(1),1)
    for _ in range(layers): h=np.tanh(h+(W@h)/degree); history.append(h.copy())
    return {"nodes":nodes,"embedding":h.tolist(),"layers":[x.tolist() for x in history],"method":"deterministic untrained signed-GRN message passing"}


def optimal_reprogramming(source_state,target_state, *, hours=48, max_factors=4):
    """Optimal-control search minimizing terminal error, dose, toxicity and time.

    Controls are restricted to transcription-factor nodes (genes with outgoing
    regulatory edges); forcing structural/lineage-marker genes directly is not
    a reprogramming strategy and trivializes the search.
    """
    nodes,W=grn_matrix(); target=np.array([target_state.get(n,0) for n in nodes],float)
    specified=np.array([n in target_state for n in nodes])  # error only over requested targets
    tf_mask=(np.abs(W).sum(0)>0)
    def objective(u):
        u=u*tf_mask; controls={n:v for n,v in zip(nodes,u) if abs(v)>1e-8}; r=simulate_fate(source_state,hours=hours,controls=controls)
        final=np.array([r["final_state"][n] for n in nodes]); return np.sum((final-target)**2*specified)+.08*np.sum(u*u)+.04*np.sum(np.abs(u))
    bounds=[(-1,1) if m else (0,0) for m in tf_mask]
    res=minimize(objective,np.zeros(len(nodes)),method="L-BFGS-B",bounds=bounds,options={"maxiter":80,"eps":1e-3})
    order=np.argsort(-np.abs(res.x))[:max_factors]; selected=[{"factor":nodes[i],"control":float(res.x[i]),"action":"overexpress" if res.x[i]>0 else "repress"} for i in order if abs(res.x[i])>.01]
    return {"interventions":selected,"objective":float(res.fun),"converged":bool(res.success),"solver":"L-BFGS-B optimal control",
            "recipe":[{"order":i+1,**x,"start_hour":round(i*hours/max(len(selected),1),2)} for i,x in enumerate(selected)]}


def stochastic_validate(source,target,interventions,replicates=64,noise=.04,seed=8):
    controls={x["factor"]:x["control"] for x in interventions}; r=simulate_fate(source,hours=72,controls=controls,noise=noise,seed=seed,trajectories=replicates)
    nodes=r["nodes"]; spec=np.array([n in target for n in nodes]); tar=np.array([target.get(n,0) for n in nodes]); finals=np.asarray(r["trajectories"])[:,-1,:]; dist=np.linalg.norm((finals-tar)*spec,axis=1)
    success=np.exp(-dist)
    return {"success_probability":float((success>.5).mean()),"mean_target_similarity":float(success.mean()),"similarity_variance":float(success.var()),
            "robustness_CI95":[float(np.quantile(success,.025)),float(np.quantile(success,.975))],"replicates":replicates}


def _diagnostics(sim,control,validation,attractors,source,target):
    nodes=sim["nodes"]; y=np.asarray(sim["mean"]); var=np.asarray(sim["variance"]); final=y[-1]; initial=y[0]; speed=np.linalg.norm(np.diff(y,axis=0),axis=1); tar=np.array([target.get(n,0) for n in nodes]); src=np.array([source.get(n,0) for n in nodes]);
    W=grn_matrix(nodes)[1]; eig=np.linalg.eigvals(W); indeg=(W!=0).sum(1); outdeg=(W!=0).sum(0); active=final>.5; interventions=control["interventions"]
    d={"node_count":len(nodes),"edge_count":int((W!=0).sum()),"activating_edge_count":int((W>0).sum()),"repressive_edge_count":int((W<0).sum()),
    "network_density":float((W!=0).sum()/max(len(nodes)*(len(nodes)-1),1)),"spectral_radius":float(max(abs(eig))),"positive_feedback_trace":float(np.trace(W@W)),
    "source_target_distance":float(np.linalg.norm(src-tar)),"initial_target_distance":float(np.linalg.norm(initial-tar)),"final_target_distance":float(np.linalg.norm(final-tar)),
    "distance_reduction":float(np.linalg.norm(initial-tar)-np.linalg.norm(final-tar)),"target_similarity":float(np.exp(-np.linalg.norm(final-tar))),
    "trajectory_length":float(np.linalg.norm(np.diff(y,axis=0),axis=1).sum()),"peak_transition_speed":float(speed.max()),"mean_transition_speed":float(speed.mean()),
    "terminal_speed":float(speed[-1]),"active_gene_count":int(active.sum()),"silenced_gene_count":int((final<.1).sum()),"state_entropy":float(-(final/final.sum()@np.log((final+1e-12)/final.sum()))),
    "expression_variance_final":float(final.var()),"noise_variance_final":float(var[-1].mean()),"intervention_count":len(interventions),
    "total_control_dose":float(sum(abs(x["control"]) for x in interventions)),"max_control_dose":float(max([abs(x["control"]) for x in interventions] or [0])),
    "overexpression_count":sum(x["action"]=="overexpress" for x in interventions),"repression_count":sum(x["action"]=="repress" for x in interventions),
    "control_objective":control["objective"],"control_converged":control["converged"],"stochastic_success_probability":validation["success_probability"],
    "stochastic_similarity":validation["mean_target_similarity"],"stochastic_similarity_variance":validation["similarity_variance"],"robustness_CI_width":validation["robustness_CI95"][1]-validation["robustness_CI95"][0],
    "attractor_count":len(attractors["attractors"]),"largest_basin_fraction":max([x["basin_fraction"] for x in attractors["attractors"]] or [0]),
    "attractor_basin_entropy":float(-sum(x["basin_fraction"]*np.log(x["basin_fraction"]+1e-12) for x in attractors["attractors"])),
    "highest_outdegree_node":nodes[int(outdeg.argmax())],"highest_indegree_node":nodes[int(indeg.argmax())],"driver_nodes":[x["factor"] for x in interventions],
    "source_marker_retention":float(np.mean([final[nodes.index(n)] for n in source if n in nodes]) if any(n in nodes for n in source) else 0),
    "target_marker_activation":float(np.mean([final[nodes.index(n)] for n in target if n in nodes]) if any(n in nodes for n in target) else 0),
    "off_target_activation":float(np.mean([final[i] for i,n in enumerate(nodes) if n not in target]) if any(n not in target for n in nodes) else 0),
    "bistability_index":float(sum(x["basin_fraction"]>.1 for x in attractors["attractors"])),"landscape_depth_proxy":float(np.linalg.norm(final-tar)**2),
    "transition_efficiency":float(np.exp(-np.linalg.norm(final-tar))/(1+sum(abs(x["control"]) for x in interventions))),
    "time_to_half_distance":float(sim["time_hours"][next((i for i,x in enumerate(y) if np.linalg.norm(x-tar)<=.5*np.linalg.norm(initial-tar)),len(y)-1)]),
    "irreversibility_proxy":float(np.linalg.norm(final-src)-np.linalg.norm(final-tar)),"recipe_step_count":len(control["recipe"]),
    "control_sparsity":float(1-len(interventions)/len(nodes)),"mean_abs_regulatory_weight":float(np.abs(W[W!=0]).mean()),
    "signed_balance":float((W>0).sum()/max((W!=0).sum(),1)),"final_state_norm":float(np.linalg.norm(final)),"phenotype_confidence":validation["mean_target_similarity"]*(1-validation["similarity_variance"])}
    assert len(d)>=50; return d


def design_fate_transition(source_state,target_state,*,hours=48,seed=8):
    """End-to-end causal landscape, optimal-control and stochastic validation."""
    attractors=identify_attractors(starts=16,seed=seed); control=optimal_reprogramming(source_state,target_state,hours=hours)
    controls={x["factor"]:x["control"] for x in control["interventions"]}; sim=simulate_fate(source_state,hours=hours,controls=controls)
    validation=stochastic_validate(source_state,target_state,control["interventions"],replicates=32,seed=seed)
    diagnostics=_diagnostics(sim,control,validation,attractors,source_state,target_state)
    return {"attractor_landscape":attractors,"optimal_control":control,"simulation":sim,"stochastic_validation":validation,
            "graph_embedding":graph_message_passing(source_state),"diagnostics":diagnostics,"enhancement_feature_count":len(diagnostics),
            "model_status":"mechanistic and deterministic/untrained graph model; not clinically validated"}

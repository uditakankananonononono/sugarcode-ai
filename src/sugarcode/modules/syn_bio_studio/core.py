from __future__ import annotations
import math
import numpy as np
from scipy.integrate import solve_ivp
PARTS={'promoter':{'weak':.2,'medium':.6,'strong':1.0},'rbs':{'weak':.2,'medium':.6,'strong':1.0},'degradation':{'slow':.05,'medium':.2,'fast':.6}}
def compile_circuit(behavior,inputs=(),parts=None):
 p=parts or {}
 architectures={'NOT':['input','repressor','output'],'AND':['input_a','input_b','coactivator','output'],'toggle':['repressor_A','repressor_B'],'oscillator':['repressor_A','repressor_B','repressor_C'],'sensor':['ligand_receptor','promoter','output']}
 if behavior not in architectures:
  raise ValueError(f"unknown behavior {behavior!r}; have {sorted(architectures)} (was: silently compiled 'sensor' under the caller's label)")
 key=behavior; return {'behavior':behavior,'nodes':architectures[key],'parts':p,'edges':[{'source':a,'target':b,'relation':'regulates'} for a,b in zip(architectures[key],architectures[key][1:])],'inputs':list(inputs),'status':'architecture-level, non-procedural'}
def hill(x,k=.5,n=2,repression=False):
 y=x**n/(k**n+x**n); return 1-y if repression else y
def simulate_toggle(hours=48,initial=(.1,.9),alpha=1,beta=.2,k=.5,n=3):
 def rhs(t,y): return [alpha*hill(y[1],k,n,True)-beta*y[0],alpha*hill(y[0],k,n,True)-beta*y[1]]
 t=np.linspace(0,hours,241); s=solve_ivp(rhs,(0,hours),initial,t_eval=t,rtol=1e-8,atol=1e-9); return {'time_h':t.tolist(),'A':s.y[0].tolist(),'B':s.y[1].tolist(),'bistable_proxy':abs(s.y[0,-1]-s.y[1,-1])}
def simulate_oscillator(hours=48,initial=(.1,.2,.3),alpha=2,beta=.5):
 def rhs(t,y): return [alpha*hill(y[2],1,3,True)-beta*y[0],alpha*hill(y[0],1,3,True)-beta*y[1],alpha*hill(y[1],1,3,True)-beta*y[2]]
 t=np.linspace(0,hours,481); s=solve_ivp(rhs,(0,hours),initial,t_eval=t,rtol=1e-8,atol=1e-9); peaks=sum(s.y[0,i]>s.y[0,i-1] and s.y[0,i]>s.y[0,i+1] for i in range(1,len(t)-1))
 y=s.y[0]; q=len(y)//4; amp_first=float(np.ptp(y[:q])); amp_last=float(np.ptp(y[-q:]))
 # the raw amplitude/peak_count are transient-dominated: at the defaults the
 # repressilator is damped (first quarter 1.36, last 0.40) - say so
 return {'time_h':t.tolist(),'species':s.y.tolist(),'peak_count':peaks,'amplitude':float(np.ptp(y)),
 'amplitude_first_quarter':amp_first,'amplitude_last_quarter':amp_last,
 'sustained_oscillation':bool(amp_last>0.5*amp_first and amp_last>0.1),
 'dynamics_note':'sustained limit cycle' if (amp_last>0.5*amp_first and amp_last>0.1) else 'damped: amplitude decays across the window; transient peaks are not evidence of sustained oscillation'}
def gillespie_expression(duration=100,transcription=2,translation=5,mrna_decay=.3,protein_decay=.1,seed=0):
 if duration<=0: raise ValueError("duration must be positive (was: nan noise_cv on an empty trace)")
 rates0=[transcription,mrna_decay*0,translation*0,protein_decay*0]
 if sum(rates0)<=0: raise ValueError("no reactions possible at the initial state (transcription 0, no molecules) - total propensity is zero")
 rng=np.random.default_rng(seed); t=0.; m=p=0; trace=[]
 while t<duration:
  rates=[transcription,mrna_decay*m,translation*m,protein_decay*p]; z=sum(rates); t+=rng.exponential(1/z); q=rng.random()*z; c=0
  for i,r in enumerate(rates):
   c+=r
   if q<=c:
    if i==0:m+=1
    elif i==1 and m:m-=1
    elif i==2:p+=1
    elif p:p-=1
    trace.append({'time':t,'mrna':m,'protein':p}); break
 return {'trace':trace,'final_mrna':m,'final_protein':p,'noise_cv':float(np.std([x['protein'] for x in trace])/max(1,np.mean([x['protein'] for x in trace])))}
def sequence_context(operator_spacing,gc_fraction,mrna_pairing):
 spacing=math.exp(-((operator_spacing-10.5)/5)**2); expression=spacing*(1-.6*abs(gc_fraction-.5))*(1-.7*mrna_pairing); return {'operator_spacing_score':spacing,'expression_factor':expression,'gc_fraction':gc_fraction,'mrna_pairing':mrna_pairing}
def host_burden(protein_production,transcription,host_capacity=100):
 load=(protein_production+transcription)/host_capacity; return {'resource_load':load,'growth_fraction':1/(1+load),'stability_risk':min(1,load*.7)}
def evolution_stability(generations,mutation_rate,selection_cost):
 survive=[math.exp(-(mutation_rate+selection_cost)*g) for g in range(generations+1)]; return {'generations':list(range(generations+1)),'intact_fraction':survive,'half_life_generations':math.log(2)/max(1e-12,mutation_rate+selection_cost)}
def assembly_plan(parts,method='Golden Gate'):
 return {'method':method,'ordered_parts':list(parts),'junction_count':max(0,len(parts)-1),'compatibility_checks':['unique junctions','orientation','reading frame'],'status':'assembly plan only; sequence-level verification required'}
def circuit_report(behavior='toggle'):
 if behavior not in ('toggle','oscillator'): raise ValueError("circuit_report simulates only 'toggle' and 'oscillator' (was: any other behavior silently got the repressilator simulation)")
 sim=simulate_toggle() if behavior=='toggle' else simulate_oscillator(); return {'architecture':compile_circuit(behavior),'simulation':sim,'stochastic':gillespie_expression(seed=1),'host':host_burden(20,5),'evolution':evolution_stability(100,.001,.005),'assembly':assembly_plan(['promoter','RBS','CDS','terminator']),'model_status':'Explicit ODE, Gillespie, resource and evolution models; no learned circuit model and no synthesis-ready sequence.'}
def studio_diagnostics(report):
 s=report['simulation']; st=report['stochastic']; h=report['host']; e=report['evolution']; return {'node_count':float(len(report['architecture']['nodes'])),'edge_count':float(len(report['architecture']['edges'])),'trajectory_points':float(len(s['time_h'])),'dynamic_range':float(s.get('bistable_proxy',s.get('amplitude',0))),'oscillation_peaks':float(s.get('peak_count',0)),'stochastic_events':float(len(st['trace'])),'final_mrna':float(st['final_mrna']),'final_protein':float(st['final_protein']),'noise_cv':st['noise_cv'],'resource_load':h['resource_load'],'growth_fraction':h['growth_fraction'],'stability_half_life':e['half_life_generations']}

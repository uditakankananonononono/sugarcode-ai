from __future__ import annotations
import math,time
from ..neuro_hub.core import dashboard as legacy_dashboard, initiate_search, recent_projects, register_project

def platform_health(module_records):
 total=len(module_records); online=sum(bool(x.get('importable',False)) for x in module_records); latency=[float(x.get('latency_ms',0)) for x in module_records]; return {'modules_total':total,'modules_online':online,'global_flux':online/max(1,total),'latency_mean_ms':sum(latency)/max(1,total),'latency_max_ms':max(latency,default=0),'degraded':[x.get('module') for x in module_records if not x.get('importable',False)]}
def compute_flux_series(samples):
 return {'timestamps':[x['timestamp'] for x in samples],'global_flux':[x['modules_online']/max(1,x['modules_total']) for x in samples],'trend':(samples[-1]['modules_online']/max(1,samples[-1]['modules_total'])-samples[0]['modules_online']/max(1,samples[0]['modules_total'])) if samples else 0}
def unified_search(query,module_results,limit=10):
 terms=query.lower().split(); scored=[]
 for r in module_results:
  text=' '.join(str(v) for v in r.values()).lower(); score=sum(text.count(t) for t in terms); 
  if score: scored.append({**r,'relevance':score})
 return {'query':query,'results':sorted(scored,key=lambda x:-x['relevance'])[:limit],'sources':sorted({r.get('module','unknown') for r in scored})}
_STATES={'created':0,'running':.5,'completed':1,'failed':0}
def project_state(name,module,state='created',artifacts=None):
 if state not in _STATES: raise ValueError(f"unknown project state {state!r}; expected one of {sorted(_STATES)}")
 return {'name':name,'module':module,'state':state,'artifacts':list(artifacts or []),'updated_at':time.time(),'completion':{'created':0,'running':.5,'completed':1,'failed':0}.get(state,0)}
def dashboard_snapshot(module_records,projects=(),search_results=()):
 health=platform_health(module_records); return {'platform':'SugarCode AI','health':health,'projects':sorted(projects,key=lambda x:-x.get('updated_at',0))[:10],'search_index_size':len(search_results),'alerts':[f"{len(health['degraded'])} modules degraded"] if health['degraded'] else [],'model_status':'Direct registry/telemetry aggregation; no neural inference model and no claim that unobserved services are healthy.'}
def dashboard_diagnostics(snapshot):
 h=snapshot['health']; return {'modules_total':float(h['modules_total']),'modules_online':float(h['modules_online']),'global_flux':h['global_flux'],'latency_mean':h['latency_mean_ms'],'latency_max':h['latency_max_ms'],'degraded_count':float(len(h['degraded'])),'project_count':float(len(snapshot['projects'])),'search_index_size':float(snapshot['search_index_size']),'alert_count':float(len(snapshot['alerts']))}

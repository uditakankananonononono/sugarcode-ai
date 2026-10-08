"""Opt-in verified registry checkpoint and operator recovery plan only.

Legacy direct writes, interprocess lost updates, dispatch TOCTOU, gate revoke
races and crash-atomic activation are unchanged. Checkpoint assumes a quiet
cooperative registry; it rechecks source bytes but is not a writer lease.
Hash metadata proves internal consistency, not authenticity against an actor
able to rewrite both payload and hashes. Never applies a recovery plan.
"""
import hashlib,json,os,tempfile
from pathlib import Path

def _digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def _validate(payload):
    data=payload['registry'];active=payload['active_files']
    if payload.get('format')!=1 or payload['payload_sha256']!=_digest({'registry':data,'active_files':active}):raise ValueError('checkpoint checksum mismatch')
    if not isinstance(data,dict) or not isinstance(data.get('module'),str) or not isinstance(data.get('features'),dict) or not isinstance(data.get('proposals'),dict):raise ValueError('registry structure mismatch')
    required={}
    for name,feature in data['features'].items():
        if not isinstance(name,str) or not isinstance(feature,dict) or not isinstance(feature.get('versions'),list):raise ValueError('invalid feature')
        version=feature.get('active_version')
        if version is None:continue
        entries=[v for v in feature['versions'] if v.get('version')==version]
        if len(entries)!=1:raise ValueError('active version not uniquely present')
        required[name]=entries[0]
    if set(required)!=set(active):raise ValueError('active feature evidence mismatch')
    for name,entry in required.items():
        record=active[name]
        if record['version']!=entry['version'] or record['sha256']!=entry['sha256'] or hashlib.sha256(record['code'].encode()).hexdigest()!=entry['sha256']:raise ValueError('active code checksum mismatch')
    return len(required)

def checkpoint(registry,destination):
    out=Path(destination)
    if out.exists() or out.is_symlink():raise FileExistsError('new checkpoint required')
    before=registry._path.read_bytes();data=json.loads(before);active={}
    for name,feature in data['features'].items():
        version=feature['active_version']
        if version is None:continue
        entry=next(v for v in feature['versions'] if v['version']==version)
        path=registry._contained(Path(entry['file']))
        if path.is_symlink() or not path.is_file():raise ValueError('real active code required')
        code=path.read_bytes()
        if hashlib.sha256(code).hexdigest()!=entry['sha256']:raise ValueError('active code changed')
        active[name]={'version':version,'sha256':entry['sha256'],'code':code.decode('utf-8')}
    if registry._path.read_bytes()!=before:raise ValueError('registry changed during checkpoint')
    payload={'format':1,'registry':data,'active_files':active,'payload_sha256':_digest({'registry':data,'active_files':active})}
    _validate(payload);out.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.registry-stage-',dir=out.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(payload,stream,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())
        os.link(tmp,out)
    finally:Path(tmp).unlink(missing_ok=True)
    return inspect_snapshot(out)

def inspect_snapshot(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('real checkpoint required')
    payload=json.loads(path.read_text());count=_validate(payload)
    return {'status':'verified','active_features_verified':count,'payload_sha256':payload['payload_sha256'],'applied':False}

def recovery_plan(path):
    inspect_snapshot(path);payload=json.loads(Path(path).read_text());_validate(payload)
    return {'action':'operator_review','applied':False,'registry':payload['registry'],
            'active_files':payload['active_files'],'limits':['original paths may be stale','proposal and inactive file contents not archived','legacy transaction and TOCTOU limits remain']}

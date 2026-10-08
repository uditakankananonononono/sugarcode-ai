"""Immutable terminal queue receipt and later-corruption checks.

Captures current trusted DB content, not cryptographic authenticity or proof
of effects. A malicious writer can alter DB and receipt together. No queue
mutation, automatic retry, effects completion or exactly-once guarantee.
"""
import hashlib,json,os,tempfile
from pathlib import Path
_FIELDS=('id','sha256','state','timeout','stdout','stderr','exit_code')
_TERMINAL={'succeeded','failed','timed_out','cancelled'}

def _canonical(record):return json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False)

def _record(queue,job_id):
    job=queue.get(job_id)
    if job['state'] not in _TERMINAL:raise ValueError('pending/running/uncertain job cannot be terminal receipt')
    if not isinstance(job['code'],str) or hashlib.sha256(job['code'].encode()).hexdigest()!=job['sha256']:raise ValueError('job code checksum mismatch')
    record={key:job[key] for key in _FIELDS}
    for field in ('stdout','stderr'):
        text=record[field]
        if text is not None and not isinstance(text,str):raise ValueError('result text type invalid')
        data=(text or '').encode();record[field+'_bytes']=len(data);record[field+'_sha256']=hashlib.sha256(data).hexdigest()
    record['effects_verified']=False
    record['receipt_sha256']=hashlib.sha256(_canonical(record).encode()).hexdigest()
    return record

def _read(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>3_000_000:raise ValueError('real bounded receipt required')
    record=json.loads(path.read_text());digest=record.pop('receipt_sha256',None)
    if hashlib.sha256(_canonical(record).encode()).hexdigest()!=digest:raise ValueError('receipt checksum mismatch')
    record['receipt_sha256']=digest
    return record

def capture(queue,job_id,destination):
    out=Path(destination)
    if out.exists() or out.is_symlink():raise FileExistsError('new receipt required')
    record=_record(queue,job_id);out.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.job-receipt-',dir=out.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            stream.write(_canonical(record)+'\n');stream.flush();os.fsync(stream.fileno())
        os.link(tmp,out)
    finally:Path(tmp).unlink(missing_ok=True)
    return record

def verify(queue,path):
    record=_read(path)
    if record!=_record(queue,record['id']):raise ValueError('current database differs from captured receipt')
    return {'status':'verified','job_id':record['id'],'state':record['state'],'effects_verified':False,'authenticity_verified':False}

def export_json(path):return _canonical(_read(path))+'\n'

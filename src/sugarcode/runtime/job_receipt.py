"""Immutable terminal queue receipt and later-corruption checks.

Captures current trusted DB content, not cryptographic authenticity or proof
of effects. A malicious writer can alter DB and receipt together. No queue
mutation, automatic retry, effects completion or exactly-once guarantee.
"""
import hashlib,json,math,os,re,tempfile
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
    try:
        with path.open('rb') as stream:raw=stream.read(3_000_001)
        if len(raw)>3_000_000:raise ValueError('receipt size cap exceeded')
        record=json.loads(raw)
    except (RecursionError,UnicodeDecodeError,MemoryError) as exc:raise ValueError('receipt JSON resource/encoding refusal') from exc
    expected=set(_FIELDS)|{'stdout_bytes','stdout_sha256','stderr_bytes','stderr_sha256','effects_verified','receipt_sha256'}
    if not isinstance(record,dict) or set(record)!=expected:raise ValueError('receipt field shape mismatch')
    if not isinstance(record['id'],str) or not record['id'] or not isinstance(record['state'],str) or record['state'] not in _TERMINAL or record['effects_verified'] is not False:raise ValueError('receipt identity/state mismatch')
    if type(record['timeout']) not in (int,float) or not math.isfinite(record['timeout']) or record['timeout']<=0:raise ValueError('receipt timeout invalid')
    if record['exit_code'] is not None and type(record['exit_code']) is not int:raise ValueError('receipt exit code invalid')
    for field in ('sha256','stdout_sha256','stderr_sha256','receipt_sha256'):
        if not isinstance(record[field],str) or not re.fullmatch('[0-9a-f]{64}',record[field]):raise ValueError('receipt hash invalid')
    for field in ('stdout','stderr'):
        if record[field] is not None and not isinstance(record[field],str):raise ValueError('receipt output type invalid')
        try:data=(record[field] or '').encode()
        except UnicodeEncodeError as exc:raise ValueError('receipt output encoding invalid') from exc
        if type(record[field+'_bytes']) is not int or record[field+'_bytes']!=len(data) or record[field+'_sha256']!=hashlib.sha256(data).hexdigest():raise ValueError('receipt output checksum mismatch')
    digest=record.pop('receipt_sha256')
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

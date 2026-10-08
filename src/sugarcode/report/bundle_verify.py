"""New checked bundle interface; legacy exporters remain unchanged.

Local cooperative publication only, not hostile-directory protection or a
power-loss durability guarantee. No recipient messages or network effects.
"""
import hashlib,json,os,shutil,tempfile
from pathlib import Path

def _name(name):
 if not isinstance(name,str) or not name or name in {'.','..','MANIFEST.json'} or '/' in name or '\\' in name or '\x00' in name:raise ValueError('unsafe artifact name')
 return name

def verify(directory):
 directory=Path(directory)
 if directory.is_symlink() or not directory.is_dir():raise ValueError('bundle must be a real directory')
 manifest_path=directory/'MANIFEST.json'
 if manifest_path.is_symlink() or not manifest_path.is_file():raise ValueError('real manifest required')
 m=json.loads(manifest_path.read_text());files=m['files']
 if not isinstance(files,dict) or not files:raise ValueError('nonempty file manifest required')
 if {p.name for p in directory.iterdir()}!=set(files)|{'MANIFEST.json'}:raise ValueError('bundle contains unmanifested/missing artifacts')
 for name,record in files.items():
  _name(name);path=directory/name
  if path.is_symlink() or not path.is_file():raise ValueError('artifact must be real file')
  h=hashlib.sha256();total=0
  with path.open('rb') as stream:
   for chunk in iter(lambda:stream.read(65536),b''):h.update(chunk);total+=len(chunk)
  if record['sha256']!=h.hexdigest() or record['bytes']!=total:raise ValueError('artifact checksum/size mismatch')
 return {'status':'verified','files_verified':len(files),'name':m['name']}

def publish(bundle,destination):
 out=Path(destination);out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists() or out.is_symlink():raise FileExistsError('new destination required')
 artifacts=bundle['artifacts']
 if not isinstance(artifacts,dict) or not artifacts:raise ValueError('nonempty artifacts required')
 for name,a in artifacts.items():
  _name(name)
  if not isinstance(a['content'],str):raise ValueError('text artifact required')
  data=a['content'].encode()
  if a['bytes']!=len(data) or a['sha256']!=hashlib.sha256(data).hexdigest():raise ValueError('input artifact checksum/size mismatch')
 lock=Path(str(out)+'.publish-lock');fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
 stage=Path(tempfile.mkdtemp(prefix='.bundle-stage-',dir=out.parent))
 try:
  manifest={k:bundle[k] for k in ('name','created_utc','generator','metadata')};manifest['files']={n:{'sha256':a['sha256'],'bytes':a['bytes']} for n,a in artifacts.items()}
  for name,a in artifacts.items():
   with (stage/name).open('wb') as stream:stream.write(a['content'].encode());stream.flush();os.fsync(stream.fileno())
  (stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
  verify(stage)
  if out.exists() or out.is_symlink():raise FileExistsError('destination changed')
  os.rename(stage,out)
  return verify(out)
 finally:
  if stage.exists():shutil.rmtree(stage)
  lock.unlink()

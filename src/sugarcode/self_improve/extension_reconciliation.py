"""Read-only bounded extension evidence. No adoption/deletion/replay authority."""
import hashlib
import os
from pathlib import Path
import stat
from .source_admission import read_source_snapshot,SOURCE_CODE_BYTES

RECONCILIATION_ENTRIES=10000


def inspect_extensions(directory,state,*,registry_sha256,max_entries=RECONCILIATION_ENTRIES):
    if type(max_entries) is not int or not 1<=max_entries<=RECONCILIATION_ENTRIES:
        raise ValueError('reconciliation count must be exact int in 1..10000')
    refs={}
    for feature in state['features'].values():
        for version in feature['versions']:
            if len(refs)>=max_entries and os.path.abspath(version['file']) not in refs:
                raise ValueError('extension reconciliation reference cap exceeded')
            refs.setdefault(os.path.abspath(version['file']),[]).append(version['sha256'])
    rows=[];seen=set()
    with os.scandir(directory) as iterator:
        for item in iterator:
            if len(rows)>=max_entries:raise ValueError('extension reconciliation entry cap exceeded')
            path=Path(item.path);key=os.path.abspath(path);seen.add(key)
            row={'path':str(path),'referenced':key in refs}
            if not stat.S_ISREG(item.stat(follow_symlinks=False).st_mode):
                row['classification']='nonregular'
            else:
                row['classification']='publish_temp' if '.publish-' in path.name and path.name.endswith('.tmp') else ('referenced' if key in refs else 'unreferenced')
                try:
                    snapshot=read_source_snapshot(path,max_bytes=SOURCE_CODE_BYTES)
                    row.update(sha256=snapshot.sha256,bytes=len(snapshot.content))
                    if key in refs and any(digest!=snapshot.sha256 for digest in refs[key]):
                        row['classification']='referenced_mismatch'
                except (ValueError,OSError) as exc:
                    row.update(classification='read_refused',error_type=type(exc).__name__)
            rows.append(row)
    for key in refs.keys()-seen:
        if len(rows)>=max_entries:raise ValueError('extension reconciliation entry cap exceeded')
        rows.append({'path':key,'referenced':True,'classification':'referenced_missing'})
    return {'registry_sha256':registry_sha256,'entries':sorted(rows,key=lambda row:row['path']),
            'read_only':True}

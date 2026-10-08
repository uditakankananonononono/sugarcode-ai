"""Read-only bounded journal inspection, never silently repairs or drops data.

A partial tail is only unterminated, invalid JSON. Semantic errors and any
newline-terminated bad record are corruption. Verified prefix is a proposed
recovery boundary for operator review, not authorization to truncate.
"""
import hashlib,json,math
from pathlib import Path
from .events import GAP_KINDS

def inspect_journal(path,*,module_slug=None,max_line_bytes=1_048_576):
    if type(max_line_bytes) is not int or max_line_bytes<=0:raise ValueError('positive line limit required')
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('real journal file required')
    slug=module_slug or path.name.removesuffix('.gap-events.jsonl')
    count=offset=0;seen=set();digest=hashlib.sha256();status='verified';error=None
    line_number=0
    try:
        with path.open('rb') as stream:
            line_number=0
            while True:
                line=stream.readline(max_line_bytes+1)
                if not line:break
                line_number+=1
                if len(line)>max_line_bytes:status='limit_exceeded';error=line_number;break
                try:raw=json.loads(line)
                except RecursionError:
                    status='depth_exceeded';error=line_number;break
                except (ValueError,UnicodeDecodeError):
                    status='corrupt' if line.endswith(b'\n') else 'partial_tail';error=line_number;break
                try:
                    if not isinstance(raw,dict) or raw.get('module_slug')!=slug:raise ValueError()
                    if not isinstance(raw.get('signature'),str) or not raw['signature'].strip():raise ValueError()
                    if raw.get('kind','capability_miss') not in GAP_KINDS:raise ValueError()
                    stamp=raw.get('at',0)
                    if type(stamp) not in (int,float) or not math.isfinite(stamp):raise ValueError()
                    eid=raw.get('event_id')
                    if eid is not None:
                        if not isinstance(eid,str) or not eid or eid in seen:raise ValueError()
                        seen.add(eid)
                except (ValueError,TypeError):status='corrupt';error=line_number;break
                digest.update(line);offset+=len(line);count+=1
    except RecursionError:status='depth_exceeded';error=max(1,line_number)
    except MemoryError:status='resource_exceeded';error=max(1,line_number)
    except OSError:status='io_error';error=max(1,line_number)
    except UnicodeDecodeError:status='corrupt';error=max(1,line_number)
    return {'status':status,'verified_prefix_events':count,'verified_prefix_bytes':offset,
            'prefix_sha256':digest.hexdigest(),'error_line':error,'mutation_performed':False}

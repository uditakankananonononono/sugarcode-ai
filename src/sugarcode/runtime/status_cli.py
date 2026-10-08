"""Read-only row-limited operational view of an existing queue DB."""
import json,sqlite3
from pathlib import Path
from .job_queue import Queue

def execute(args):
    try:
        # Do not create or migrate databases merely to inspect status.
        path=Path(args.db).resolve()
        if not path.is_file():raise ValueError('existing queue database required')
        q=object.__new__(Queue)
        q.path=path
        def readonly():
            db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;return db
        q._db=readonly
        print(json.dumps({'jobs':q.status(state=args.state,limit=args.limit)},allow_nan=False));return 0
    except (ValueError,OSError,sqlite3.Error) as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__}));return 1

def register(sub):
    p=sub.add_parser('queue-status',help='read-only queue metadata, excludes script/output')
    p.add_argument('--db',required=True);p.add_argument('--state');p.add_argument('--limit',type=int,default=100);p.set_defaults(func=execute)

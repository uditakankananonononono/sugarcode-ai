"""Opt-in product CLI for trusted local scripts, never implicit execution.

Queue is NOT a security sandbox. submit only records; run is a separate
explicit command. Receipts detect later corruption, not effects/authenticity.
"""
import json
from pathlib import Path
from .job_queue import Queue
from .job_receipt import capture,verify

def execute(args):
    try:
        q=Queue(args.db)
        if args.queue_action=='submit':
            path=Path(args.script)
            if path.stat().st_size>1_048_576:raise ValueError('script cap exceeded')
            result={'job_id':q.submit(args.job_id,path.read_text(),timeout=args.timeout),'state':'pending','trusted_script_only':True}
        elif args.queue_action=='run':result={'job_id':q.run_next(),'effects_verified':False}
        elif args.queue_action=='show':result=q.get(args.job_id)
        elif args.queue_action=='cancel':result={'cancelled':q.cancel(args.job_id)}
        elif args.queue_action=='receipt':result=capture(q,args.job_id,args.out)
        else:result=verify(q,args.receipt)
        print(json.dumps(result,sort_keys=True,allow_nan=False));return 0
    except (ValueError,KeyError,OSError) as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__,'message':str(exc)[:200]}));return 1

def register(subparsers):
    p=subparsers.add_parser('queue',help='trusted local script queue (NOT isolated; explicit run only)')
    p.add_argument('--db',required=True);sub=p.add_subparsers(dest='queue_action',required=True)
    a=sub.add_parser('submit');a.add_argument('job_id');a.add_argument('--script',required=True);a.add_argument('--timeout',type=float,default=30)
    sub.add_parser('run')
    for name in ('show','cancel'):
        a=sub.add_parser(name);a.add_argument('job_id')
    a=sub.add_parser('receipt');a.add_argument('job_id');a.add_argument('--out',required=True)
    a=sub.add_parser('verify');a.add_argument('--receipt',required=True)
    p.set_defaults(func=execute)

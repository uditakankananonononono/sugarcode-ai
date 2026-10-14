"""Row523 Backup Strategy - Protects data.
Determine reconstructible backup chains and best recoverable timestamp from
supplied backup metadata and availability flags. Backup tuple is (timestamp,
parent index or None, byte size, available bool); None parent is a full backup,
otherwise it is an incremental requiring every ancestor. Timestamp strictly
increases along edges, cycles are refused. Best <= requested timestamp chooses
latest timestamp, lowest total chain bytes, then lex root-to-leaf index chain.
0..64 backups; timestamp0..10**9, bytes0..10**12. Requested timestamp0..10**9.
NOT_CLAIMED: stored bytes, backup integrity, actual protection, live restore,
retention policy, encryption, external effects or disaster readiness.
"""

def recover(backups,requested):
    if type(backups) is not list or len(backups)>64:raise ValueError('0..64 backups before scan')
    if type(requested) is not int or not 0<=requested<=10**9:raise ValueError('requested integer0..1000000000')
    n=len(backups)
    for row in backups:
        if type(row) is not tuple or len(row)!=4:raise ValueError('backup timestamp parent bytes available quadruple')
        ts,parent,size,available=row
        if type(ts) is not int or not 0<=ts<=10**9:raise ValueError('timestamp integer0..1000000000')
        if parent is not None and (type(parent) is not int or not 0<=parent<n):raise ValueError('parent None or valid integer index')
        if type(size) is not int or not 0<=size<=10**12:raise ValueError('bytes integer0..1000000000000')
        if type(available) is not bool:raise ValueError('available must be bool')
    for i,(ts,parent,size,available) in enumerate(backups):
        if parent is not None and backups[parent][0]>=ts:raise ValueError('parent timestamp must be strictly earlier')
    chains=[];options=[]
    for i,(ts,parent,size,available) in enumerate(backups):
        path=[];cursor=i;good=True
        while cursor is not None:
            path.append(cursor)
            if not backups[cursor][3]:good=False
            cursor=backups[cursor][1]
        chain=tuple(reversed(path)) if good else None;chains.append(chain)
        if chain is not None and ts<=requested:
            total=sum(backups[j][2] for j in chain)
            options.append((-ts,total,chain))
    if options:
        neg,total,chain=min(options);best={'timestamp':-neg,'chain':chain,'bytes_to_read':total,'data_loss_window':requested+neg}
    else:best=None
    return {'recoverable_chains':chains,'best':best,'data_protected_externally':False}

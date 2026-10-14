"""Industrial Ecology.

PARTIAL: caller input/output/loss material ledger only, not industrial
ecology, industrial symbiosis, lifecycle analysis or environmental benefit.
Caller compatible quantities are abstract, not verified industrial process data.
"""
SCOPE='caller input-output-loss material ledger only; no industrial ecology claims'


def balances(rows):
    """Exactlist/tuple1..64 quads(label,input,output,loss);printable Unicode
    exactstr labels1..40,repeats aggregate;exactint quantities0..1000000.
    Sorted(label,input sum,output sum,loss sum,signed residual),total residual
    and strictly negative residual labels. Negative values retained.
    Mixedrows accepted;no process interactions,chemistry,stock carryover or units inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,quantity,output,loss=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(quantity) is not int or type(output) is not int or type(loss) is not int or not 0<=quantity<=1000000 or not 0<=output<=1000000 or not 0<=loss<=1000000:raise ValueError('quantities must be exactint0..1000000')
        q,u,l=groups.get(label,(0,0,0));groups[label]=(q+quantity,u+output,l+loss)
    result=tuple((label,q,u,l,q-u-l) for label,(q,u,l) in sorted(groups.items()))
    return {'balances':result,'total_residual':sum(row[4] for row in result),'negative':tuple(row[0] for row in result if row[4]<0),'scope':SCOPE}

"""One-pass minibatch SGD for supplied linear-regression batches.
NOT_CLAIMED: authentic data; shuffled/IID stream; generalization; full-stream
convergence; large-data throughput benchmark; real-world or external execution.
"""
import math


def train(batches,initial,rate,max_batches):
    if type(max_batches) is not int or not 1<=max_batches<=100:raise ValueError('strict max batches 1..100')
    if type(rate) not in (int,float) or not 0<rate<=1 or not math.isfinite(rate):raise ValueError('strict finite learning rate (0,1]')
    if type(initial) is not list or not 1<=len(initial)<=8:raise ValueError('1..8 initial weights before scan')
    d=len(initial)
    def number(v):
        if type(v) not in (int,float) or not -1000<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite regression value within -1000..1000')
        return float(v)
    w=[number(v) for v in initial]
    try:stream=iter(batches)
    except TypeError:raise ValueError('iterable batch stream required') from None
    history=[];seen=0;exhausted=False
    for index in range(max_batches):
        try:batch=next(stream)
        except StopIteration:exhausted=True;break
        if type(batch) is not list or not 1<=len(batch)<=128:raise ValueError('1..128 samples per batch before scan')
        data=[]
        for sample in batch:
            if type(sample) is not dict or set(sample)!={'features','target'}:raise ValueError('exact features/target sample fields')
            f=sample['features']
            if type(f) is not list or len(f)!=d:raise ValueError('one feature per weight')
            data.append(([number(v) for v in f],number(sample['target'])))
        n=len(data)
        residual=[math.fsum(a*b for a,b in zip(w,f))-y for f,y in data]
        gradient=[math.fsum(r*f[j] for r,(f,y) in zip(residual,data))/n for j in range(d)]
        norm_bound=math.fsum(math.fsum(v*v for v in f) for f,y in data)/n
        effective=rate/max(1,norm_bound)
        new=[v-effective*g for v,g in zip(w,gradient)]
        if any(not math.isfinite(v) for v in new):raise ValueError('finite numerical weights required')
        after=[math.fsum(a*b for a,b in zip(new,f))-y for f,y in data]
        history.append({'batch_index':index,'samples':n,'gradient':gradient,'effective_rate':effective,
                        'loss_before':math.fsum(r*r for r in residual)/(2*n),'loss_after':math.fsum(r*r for r in after)/(2*n)})
        w=new;seen+=n
    if not history:raise ValueError('at least one training batch required')
    return {'weights':w,'batches_used':len(history),'samples_seen':seen,'batch_history':history,'stream_exhausted_observed':exhausted,
            'stream_fully_consumed_claimed':exhausted,'retained_sample_cap':128,'method':'streaming_minibatch_SGD_trace_normalized_rate',
            'loss_definition':'mean half squared prediction error per batch; no intercept unless feature supplied',
            'full_dataset_loss_computed':False,'external_effects':[]}

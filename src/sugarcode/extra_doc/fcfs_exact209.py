"""Exact finite FCFS multi-server queue on supplied arrival/service events.
NOT_CLAIMED: authentic arrivals/service times; fitted stochastic process;
real-queue forecast; real-world execution; runtime integration.
"""
from fractions import Fraction
import heapq
import math


def simulate(jobs,servers):
    if type(servers) is not int or not 1<=servers<=20:raise ValueError('strict integer servers 1..20')
    if type(jobs) is not list or not 1<=len(jobs)<=1000:raise ValueError('1..1000 queue jobs before scan')
    parsed=[];seen=set()
    for row in jobs:
        if type(row) is not dict or set(row)!={'id','arrival','service'}:raise ValueError('exact id/arrival/service fields')
        label=row['id']
        if type(label) is not str or not 1<=len(label)<=120 or not label.strip():raise ValueError('bounded nonblank job id')
        if label in seen:raise ValueError('distinct job ids')
        seen.add(label);numbers=[]
        for field in ('arrival','service'):
            value=row[field]
            if type(value) not in (int,float) or not 0<=value<=1000000 or not math.isfinite(value):raise ValueError('strict finite arrival/service within 0..1000000')
            numbers.append(Fraction(str(value)))
        parsed.append((numbers[0],label,numbers[1]))
    parsed.sort();available=[(Fraction(0),i) for i in range(servers)];heapq.heapify(available);out=[];waitsum=servicesum=Fraction(0)
    for arrival,label,service in parsed:
        free,server=heapq.heappop(available);start=max(arrival,free);end=start+service;wait=start-arrival
        heapq.heappush(available,(end,server));waitsum+=wait;servicesum+=service
        out.append({'id':label,'server':server,'arrival_fraction':str(arrival),'start_fraction':str(start),
                    'completion_fraction':str(end),'wait_fraction':str(wait),'sojourn_fraction':str(wait+service)})
    horizon=max(t for t,i in available)
    return {'jobs':out,'final_clock_fraction':str(horizon),'total_wait_fraction':str(waitsum),
            'mean_wait_fraction':str(waitsum/len(jobs)),'mean_sojourn_fraction':str((waitsum+servicesum)/len(jobs)),
            'aggregate_server_utilization_fraction':str(servicesum/(servers*horizon)) if horizon else None,
            'time_average_queue_length_fraction':str(waitsum/horizon) if horizon else None,
            'discipline':'FCFS arrivals; equal arrival ties ascending id; equal available time ties lowest server index',
            'observation_window':'time zero through final completion, including idle gaps',
            'units':'arrival/service/wait/clock in supplied time units; utilization/queue length dimensionless',
            'real_queue_forecast_verified':False,'stochastic_process_fitted':False,'external_effects':[]}

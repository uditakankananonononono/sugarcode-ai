"""Row 351 Participatory Design: exact aggregation of supplied participant votes.

Aggregates supplied ranked design ballots using Borda points, reports each
participant's contribution and all tied winners. Partial ballots are allowed;
unranked candidates receive zero. No fabricated participant responses.
Caps 32 participants/eight candidates with weights zero through 1000000.
NOT_CLAIMED: actual consultation, democratic legitimacy, sampling fairness,
real user preferences, universal representation or autonomous deployment.
"""


def participatory_vote(ballots,weights,candidate_count):
    if type(ballots) not in (list,tuple) or type(weights) not in (list,tuple):
        raise TypeError('ballots and weights must be lists or tuples')
    if not 1<=len(ballots)<=32:raise ValueError('participant count must be between 1 and 32')
    if type(candidate_count) is not int or not 1<=candidate_count<=8:
        raise ValueError('candidate_count must be a nonbool integer between 1 and 8')
    if len(weights)!=len(ballots):raise ValueError('weight count must match participants')
    for ballot in ballots:
        if type(ballot) not in (list,tuple) or len(ballot)>candidate_count:
            raise ValueError('ballots must be lists or tuples no longer than candidate count')
        if any(type(i) is not int or not 0<=i<candidate_count for i in ballot):
            raise ValueError('ballot indices must be nonbool integers inside candidate range')
        if len(set(ballot))!=len(ballot):raise ValueError('ballot candidates must be unique')
    if any(type(v) is not int or not 0<=v<=1000000 for v in weights):
        raise ValueError('weights must be nonbool integers zero through 1000000')
    contributions=[];totals=[0]*candidate_count
    for ballot,weight in zip(ballots,weights):
        row=[0]*candidate_count
        for rank,candidate in enumerate(ballot):row[candidate]=weight*(candidate_count-rank)
        contributions.append(row)
        totals=[a+b for a,b in zip(totals,row)]
    maximum=max(totals);winners=[i for i,v in enumerate(totals) if v==maximum]
    return {'scores':totals,'participant_contributions':contributions,'winner_indices':winners,
            'consultation_performed':False}

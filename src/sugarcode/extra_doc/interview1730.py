"""Doc row1730 Interview Design: PARTIAL topic/question sequence audit.

Topics exact list1..20 unique valid labels; questions exact list0..50 tuples
(id,topic,minutes), unique IDs, topic valid label, minutes exact int1..60.
Labels nonblank exact str<=80. Return uncovered topics, unknown question IDs,
revisited topic blocks (each topic appearing in more than one contiguous run,
listed in topic input order), total minutes. No interviewing/wording quality.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit(topics,questions):
    if type(topics) is not list or not 1<=len(topics)<=20:
        raise ValueError('topics must be an exact list with 1..20 entries')
    if any(not _label(x) for x in topics) or len(set(topics))!=len(topics):
        raise ValueError('topics must be unique valid labels')
    if type(questions) is not list or len(questions)>50:
        raise ValueError('questions must be an exact list with 0..50 entries')
    ids=set()
    for row in questions:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('question must be an id topic minutes tuple')
        name,topic,minutes=row
        if not _label(name) or name in ids:raise ValueError('question IDs must be unique valid labels')
        ids.add(name)
        if not _label(topic):raise ValueError('question topic must be a valid label')
        if type(minutes) is not int or not 1<=minutes<=60:raise ValueError('minutes must be an integer in 1..60')
    runs={t:0 for t in topics};previous=None;unknown=[]
    for name,topic,_ in questions:
        if topic in runs:
            if topic!=previous:runs[topic]+=1
        else:unknown.append(name)
        previous=topic
    return {'uncovered':[t for t in topics if runs[t]==0],'revisited':[t for t in topics if runs[t]>1],
            'unknown':unknown,'minutes':sum(m for n,t,m in questions),'claim':'PARTIAL','interview_validated':False}

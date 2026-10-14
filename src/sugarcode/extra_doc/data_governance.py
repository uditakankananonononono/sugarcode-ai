"""Row532 Data Governance: supplied asset-role access rule reconciliation.

Rules(role,asset,allow) use deny precedence across duplicate rules. Absent rule
means deny. Return allowed asset indices per role. Caps16roles/32assets/128rules.
NOT_CLAIMED: permissions changed, identity verified, actual governance, legal
compliance, data discovery, live access or external security enforcement.
"""


def access_matrix(role_count,asset_count,rules):
    if type(role_count) is not int or not 1<=role_count<=16:raise ValueError('role count must be nonbool integer between 1 and 16')
    if type(asset_count) is not int or not 1<=asset_count<=32:raise ValueError('asset count must be nonbool integer between 1 and 32')
    if type(rules) not in (list,tuple):raise TypeError('rules must be a list or tuple')
    if len(rules)>128:raise ValueError('at most 128 rules allowed')
    if any(type(row) not in (list,tuple) or len(row)!=3 for row in rules):raise ValueError('rules must contain role asset allow triples')
    decisions={}
    for role,asset,allow in rules:
        if type(role) is not int or not 0<=role<role_count:raise ValueError('role must be nonbool valid index')
        if type(asset) is not int or not 0<=asset<asset_count:raise ValueError('asset must be nonbool valid index')
        if type(allow) is not bool:raise TypeError('allow must be bool')
        key=(role,asset);decisions[key]=decisions.get(key,True) and allow
    return {'allowed_assets':[[a for a in range(asset_count) if decisions.get((r,a),False)] for r in range(role_count)],'permissions_changed':False}

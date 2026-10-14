import pytest
from sugarcode.extra_doc.authorization_design526 import evaluate_access, evaluate_role_policy

class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass

ACCESS = [('amy', 'doc', 'read', 1, 0), ('bob', 'doc', 'read', 0, 0)]
POLICY = [('editor', 'doc', 'read', 'allow'), ('reader', 'doc', 'read', 'deny')]
REQUESTS = [('amy', 'editor', 'doc', 'read'), ('bob', 'reader', 'doc', 'read')]

@pytest.mark.parametrize('container', [L, T])
def test_access_containers(container):
    with pytest.raises(TypeError, match='^exact list required$'):
        evaluate_access(container(ACCESS))
    with pytest.raises(TypeError, match='^exact tuple row required$'):
        evaluate_access([ACCESS[0], container(ACCESS[1])])

@pytest.mark.parametrize('slot', range(5))
def test_access_scalar_subclasses_nonfirst(slot):
    row = list(ACCESS[1]); row[slot] = S(row[slot]) if slot < 3 else I(row[slot])
    message = '^exact string label required$' if slot < 3 else '^exact nonbool integer required$'
    with pytest.raises(TypeError, match=message):
        evaluate_access([ACCESS[0], tuple(row)])

def test_duplicate_request_exact():
    with pytest.raises(ValueError, match='^duplicate request$'):
        evaluate_access([ACCESS[0], ACCESS[0]])

@pytest.mark.parametrize('container', [L, T])
@pytest.mark.parametrize('which', ['policy', 'requests'])
def test_policy_containers(container, which):
    policy, requests = list(POLICY), list(REQUESTS)
    if which == 'policy': policy = container(policy)
    else: requests = container(requests)
    with pytest.raises(TypeError, match='^exact list required$'):
        evaluate_role_policy(policy, requests)
    policy, requests = list(POLICY), list(REQUESTS)
    if which == 'policy': policy[1] = container(policy[1])
    else: requests[1] = container(requests[1])
    with pytest.raises(TypeError, match='^exact tuple row required$'):
        evaluate_role_policy(policy, requests)

@pytest.mark.parametrize('slot', range(4))
@pytest.mark.parametrize('which', ['policy', 'requests'])
@pytest.mark.parametrize('subclass', [S, I])
def test_policy_scalar_subclasses_nonfirst(slot, which, subclass):
    policy, requests = list(POLICY), list(REQUESTS)
    rows = policy if which == 'policy' else requests
    row = list(rows[1]); row[slot] = S(row[slot]) if subclass is S else I(1); rows[1] = tuple(row)
    message = '^exact string effect required$' if which == 'policy' and slot == 3 else '^exact string label required$'
    with pytest.raises(TypeError, match=message):
        evaluate_role_policy(policy, requests)

from sugarcode.modules.enterprise_bio import *
def test_budget():
 e=GovernedEntitlements('startup',monthly_budget_usd=10); assert e.authorize_spend(8,'run')['allowed']; assert not e.authorize_spend(3,'run')['allowed']
def test_export(): assert not GovernedEntitlements('academic').data_export('restricted','x')['allowed']
def test_forecast():
 e=GovernedEntitlements('startup'); e.consume_compute(100); assert e.usage_forecast(1)['over_quota']
def test_audit_digest():
 e=GovernedEntitlements('startup'); e.data_export('internal','vault'); assert len(e.audit[-1]['digest'])==64
def test_scope(): assert 'not a substitute' in GovernedEntitlements('enterprise').governance_report()['scope']

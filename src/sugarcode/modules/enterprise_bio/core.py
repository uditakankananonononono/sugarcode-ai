from __future__ import annotations

TIERS = {
    "academic": {
        "price_usd_mo": 0,
        "compute_hours_mo": 100,
        "private_vault": False,
        "robotic_lab": False,
        "modules": "core",          # core 40 modules
        "support": "community",
        "max_users": 5,
    },
    "startup": {
        "price_usd_mo": 499,
        "compute_hours_mo": 1000,
        "private_vault": True,
        "robotic_lab": False,
        "modules": "full",          # all 77
        "support": "email (next business day)",
        "max_users": 20,
    },
    "enterprise": {
        "price_usd_mo": 4999,
        "compute_hours_mo": 10000,
        "private_vault": True,
        "robotic_lab": True,
        "modules": "full+custom",
        "support": "dedicated (4h SLA)",
        "max_users": 250,
    },
}


class Entitlements:
    """Runtime gate: checks a tenant's tier before compute, vault, robot calls."""

    def __init__(self, tier: str):
        if tier not in TIERS:
            raise KeyError(f"unknown tier; have {sorted(TIERS)}")
        self.tier = tier
        self.spec = TIERS[tier]
        self._compute_used = 0.0
        self.audit: list[dict] = []

    def check_module_access(self, module_slug: str, module_index: int) -> dict:
        if self.spec["modules"] == "core" and module_index > 40:
            allowed = False
            reason = f"{module_slug} is beyond the core set - upgrade to startup/enterprise"
        else:
            allowed, reason = True, "within tier"
        self.audit.append({"check": "module", "module": module_slug, "allowed": allowed})
        return {"allowed": allowed, "reason": reason}

    def consume_compute(self, hours: float) -> dict:
        if hours <= 0:
            raise ValueError("hours must be positive")
        remaining = self.spec["compute_hours_mo"] - self._compute_used
        allowed = hours <= remaining
        if allowed:
            self._compute_used += hours
        self.audit.append({"check": "compute", "hours": hours, "allowed": allowed})
        return {"allowed": allowed,
                "remaining_hours": round(self.spec["compute_hours_mo"] - self._compute_used, 2),
                "reason": "ok" if allowed else "monthly compute quota exhausted - throttled to burst queue"}

    def use_vault(self) -> dict:
        allowed = self.spec["private_vault"]
        self.audit.append({"check": "vault", "allowed": allowed})
        return {"allowed": allowed,
                "reason": "private data vault active" if allowed
                else "private vault requires startup tier or above"}

    def dispatch_robot(self, protocol: str) -> dict:
        allowed = self.spec["robotic_lab"]
        self.audit.append({"check": "robot", "protocol": protocol, "allowed": allowed})
        return {"allowed": allowed,
                "reason": (f"protocol '{protocol}' queued on robotic flow line" if allowed
                           else "robotic lab automation is enterprise-only")}

    def tier_report(self) -> dict:
        return {"tier": self.tier, "spec": self.spec,
                "compute_used_h": round(self._compute_used, 2),
                "audit_trail": self.audit}

from datetime import datetime, timezone
import hashlib, json

class GovernedEntitlements(Entitlements):
    def __init__(self,tier,tenant_id='default',monthly_budget_usd=None):
        super().__init__(tier); self.tenant_id=tenant_id; self.monthly_budget_usd=monthly_budget_usd; self.spend_usd=0.0
    def _event(self,action,allowed,**details):
        event={'timestamp':datetime.now(timezone.utc).isoformat(),'tenant_id':self.tenant_id,'action':action,'allowed':allowed,**details}
        event['digest']=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest(); self.audit.append(event); return event
    def authorize_spend(self,amount_usd,purpose):
        if amount_usd<0: raise ValueError('amount_usd must be nonnegative')
        allowed=self.monthly_budget_usd is None or self.spend_usd+amount_usd<=self.monthly_budget_usd
        if allowed:self.spend_usd+=amount_usd
        self._event('spend',allowed,amount_usd=amount_usd,purpose=purpose)
        return {'allowed':allowed,'spend_usd':self.spend_usd,'remaining_budget_usd':None if self.monthly_budget_usd is None else self.monthly_budget_usd-self.spend_usd}
    def data_export(self,classification,destination):
        allowed=classification in ('public','internal') or self.spec['private_vault']
        self._event('data_export',allowed,classification=classification,destination=destination)
        return {'allowed':allowed,'classification':classification,'destination':destination}
    def usage_forecast(self,days_elapsed):
        if days_elapsed<=0: raise ValueError('days_elapsed must be positive')
        projected=self._compute_used/days_elapsed*30; quota=self.spec['compute_hours_mo']
        return {'projected_monthly_hours':projected,'quota_hours':quota,'over_quota':projected>quota,'utilization_fraction':projected/quota}
    def governance_report(self):
        return {'tenant_id':self.tenant_id,'tier':self.tier,'compute_used_h':self._compute_used,'spend_usd':self.spend_usd,'events':list(self.audit),'scope':'Deterministic entitlement enforcement; not a substitute for legal, privacy, or security review.'}

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

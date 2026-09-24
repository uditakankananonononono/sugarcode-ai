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


# --- governed operations: chained audit, real vault, real robot queue -------------
import os, tempfile, importlib, hmac, base64, warnings

VAULT_KEY_ENV = "SUGARCODE_VAULT_KEY"

def _load_fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:  # optional extra, see pyproject [vault]
        raise ImportError("GovernedOperations vault needs the 'cryptography' package: "
                          "pip install 'sugarcode-ai[vault]'") from exc
    return Fernet

class GovernedOperations(GovernedEntitlements):
    """GovernedEntitlements plus: hash-chained audit on every check, an encrypted
    per-tenant vault, a real robot job queue, and module-call enforcement."""

    _ROBOT_TRANSITIONS = {"queued": {"running", "cancelled"}, "running": {"done", "failed", "cancelled"}}

    def __init__(self, tier, tenant_id="default", monthly_budget_usd=None,
                 vault_dir=None, vault_key=None):
        if not tenant_id or "/" in tenant_id or "\\" in tenant_id or ".." in tenant_id:
            raise ValueError("tenant_id must be a simple identifier (it names the vault directory)")
        super().__init__(tier, tenant_id=tenant_id, monthly_budget_usd=monthly_budget_usd)
        self.vault_dir = vault_dir or os.path.join(tempfile.gettempdir(), "sugarcode_vault", tenant_id)
        # Key story: the master key comes from the vault_key argument, else the
        # SUGARCODE_VAULT_KEY env var, else a random per-process key (ephemeral:
        # data is unreadable after this object is gone; a warning is emitted).
        # The key lives only in memory; it is never written to vault_dir, the
        # audit trail, or any file. Per-tenant keys are HMAC-SHA256(master,
        # "sugarcode-vault:" + tenant_id), so one tenant's key cannot open
        # another tenant's files.
        raw = vault_key if vault_key is not None else os.environ.get(VAULT_KEY_ENV)
        if raw:
            self._vault_key = raw if isinstance(raw, bytes) else str(raw).encode()
            self.vault_key_source = "argument" if vault_key is not None else "env"
        else:
            self._vault_key = os.urandom(32)
            self.vault_key_source = "ephemeral"
        self._robot_jobs: dict[str, dict] = {}

    def verify_audit_chain(self) -> bool:
        """True only if every entry's digest matches its content and links to the previous one."""
        prev = "genesis"
        for ev in self.audit:
            body = {k: v for k, v in ev.items() if k != "digest"}
            if ev.get("prev_digest") != prev: return False
            if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != ev.get("digest"): return False
            prev = ev["digest"]
        return True

    # every check lands on the same hash-chained audit trail
    def _event(self, action, allowed, **details):
        prev = self.audit[-1].get("digest", "genesis") if self.audit else "genesis"
        return super()._event(action, allowed, prev_digest=prev, **details)

    def check_module_access(self, module_slug, module_index):
        r = super().check_module_access(module_slug, module_index)
        self.audit.pop()  # replace base-class partial entry with a governed one
        self._event("module_access", r["allowed"], module=module_slug, module_index=module_index, reason=r["reason"])
        return r

    def consume_compute(self, hours):
        r = super().consume_compute(hours)
        self.audit.pop()
        self._event("compute", r["allowed"], hours=hours, remaining_hours=r["remaining_hours"], reason=r["reason"])
        return r

    def use_vault(self):
        r = super().use_vault()
        self.audit.pop()
        self._event("vault_access", r["allowed"], reason=r["reason"])
        return r

    # encrypted vault: Fernet (AES-128-CBC + HMAC) per tenant, file-backed
    def _fernet(self):
        Fernet = _load_fernet()
        if self.vault_key_source == "ephemeral" and not getattr(self, "_warned", False):
            warnings.warn("vault key is ephemeral; pass vault_key or set SUGARCODE_VAULT_KEY to keep data readable")
            self._warned = True
        tenant_key = hmac.new(self._vault_key, b"sugarcode-vault:" + self.tenant_id.encode(), hashlib.sha256).digest()
        return Fernet(base64.urlsafe_b64encode(tenant_key))

    def vault_store(self, name: str, data) -> dict:
        if not self.spec["private_vault"]:
            self._event("vault_store", False, name=name, reason="private vault requires startup tier or above")
            return {"stored": False, "reason": "private vault requires startup tier or above"}
        if not name or "/" in name or ".." in name: raise ValueError("name must be a simple identifier")
        blob = data.encode() if isinstance(data, str) else bytes(data)
        token = self._fernet().encrypt(blob)
        os.makedirs(self.vault_dir, mode=0o700, exist_ok=True)
        path = os.path.join(self.vault_dir, name + ".enc")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as fh: fh.write(token)
        self._event("vault_store", True, name=name, bytes=len(blob))
        return {"stored": True, "name": name, "bytes": len(blob)}

    def vault_retrieve(self, name: str) -> bytes:
        if not self.spec["private_vault"]:
            self._event("vault_retrieve", False, name=name, reason="private vault requires startup tier or above")
            raise PermissionError("private vault requires startup tier or above")
        if not name or "/" in name or ".." in name: raise ValueError("name must be a simple identifier")
        path = os.path.join(self.vault_dir, name + ".enc")
        with open(path, "rb") as fh: blob = self._fernet().decrypt(fh.read())
        self._event("vault_retrieve", True, name=name, bytes=len(blob))
        return blob

    # robot queue: validated lifecycle, exportable for a lab driver
    def dispatch_robot(self, protocol: str) -> dict:
        if not protocol or not str(protocol).strip(): raise ValueError("protocol must be a non-empty name")
        r = Entitlements.dispatch_robot(self, protocol)
        self.audit.pop()
        if not r["allowed"]:
            self._event("robot_dispatch", False, protocol=protocol, reason=r["reason"])
            return r
        job_id = hashlib.sha256(f"{self.tenant_id}:{protocol}:{len(self._robot_jobs)}".encode()).hexdigest()[:12]
        self._robot_jobs[job_id] = {"job_id": job_id, "tenant_id": self.tenant_id, "protocol": protocol,
                                    "status": "queued", "submitted_at": datetime.now(timezone.utc).isoformat()}
        self._event("robot_dispatch", True, protocol=protocol, job_id=job_id)
        return {"allowed": True, "job_id": job_id, "status": "queued",
                "reason": f"protocol '{protocol}' queued on robotic flow line"}

    def robot_advance(self, job_id: str, status: str) -> dict:
        job = self._robot_jobs.get(job_id)
        if job is None: raise KeyError(f"unknown robot job {job_id!r}")
        if status not in self._ROBOT_TRANSITIONS.get(job["status"], set()):
            raise ValueError(f"cannot move job from {job['status']} to {status}")
        job["status"] = status
        self._event("robot_advance", True, job_id=job_id, status=status)
        return dict(job)

    def robot_queue(self) -> list[dict]:
        return [dict(j) for j in self._robot_jobs.values()]

    def export_robot_queue(self) -> str:
        self._event("robot_export", True, jobs=len(self._robot_jobs))
        return json.dumps({"tenant_id": self.tenant_id, "jobs": self.robot_queue()}, indent=2)

    # enforcement at a real call site: run a module function only if the tier allows it
    def guarded_module_call(self, module_slug: str, module_index: int, function: str, *args, **kwargs):
        gate = self.check_module_access(module_slug, module_index)
        if not gate["allowed"]:
            return {"called": False, "reason": gate["reason"]}
        fn = getattr(importlib.import_module(f"sugarcode.modules.{module_slug}"), function)
        result = fn(*args, **kwargs)
        self._event("module_call", True, module=module_slug, function=function)
        return {"called": True, "result": result}

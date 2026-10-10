"""Strict registry-resident consumption records, not tamper-proof consent."""
import hashlib
import json
import math

CONSUMED_KEY = 'engine_consumed_approvals'
_FIELDS = {'gate_identity','approval_id','action','feature','version','consumed_at'}
_ACTIONS = {'self_improvement_activation','self_improvement_rollback'}


def consumption_key(gate_identity: str, approval_id: str) -> str:
    for value in (gate_identity,approval_id):
        if type(value) is not str or not value:
            raise ValueError('consumption identity must be nonempty builtin string')
    return hashlib.sha256(json.dumps([gate_identity,approval_id],ensure_ascii=True,
                                     separators=(',',':')).encode()).hexdigest()


def validate_consumptions(value):
    if type(value) is not dict:
        raise ValueError('engine consumption map must be object')
    for key,record in value.items():
        if type(record) is not dict or set(record)!=_FIELDS:
            raise ValueError('invalid engine consumption record fields')
        expected=consumption_key(record['gate_identity'],record['approval_id'])
        if type(key) is not str or key!=expected:
            raise ValueError('invalid engine consumption key')
        if type(record['action']) is not str or record['action'] not in _ACTIONS:
            raise ValueError('invalid engine consumption action')
        if type(record['feature']) is not str or not record['feature']:
            raise ValueError('invalid engine consumption feature')
        if type(record['version']) is not int or record['version']<1:
            raise ValueError('invalid engine consumption version')
        timestamp=record['consumed_at']
        if type(timestamp) not in (int,float) or not math.isfinite(timestamp) or timestamp<0:
            raise ValueError('invalid engine consumption timestamp')
    return value


def add_consumption(state, *, gate_identity, approval_id, action, feature, version, consumed_at):
    records=state.setdefault(CONSUMED_KEY,{})
    validate_consumptions(records)
    key=consumption_key(gate_identity,approval_id)
    if key in records:
        raise PermissionError('approval already consumed in this registry')
    records[key]=dict(gate_identity=gate_identity,approval_id=approval_id,action=action,
                      feature=feature,version=version,consumed_at=consumed_at)
    validate_consumptions(records)

"""Opt-in checked tool calls. Legacy dispatcher/agent remain unchanged.

Validation is limited to the catalog's current small JSON-schema vocabulary.
Unknown schema keywords fail closed rather than pretending full JSON Schema.
This validates arguments, not authorization or tool isolation.
"""
import json,math
from . import tools

def _validate(value,schema,path='arguments'):
    supported={'type','nullable','default','items','additionalProperties','properties','required'}
    if set(schema)-supported:raise ValueError('unsupported schema keyword')
    if value is None and schema.get('nullable'):return
    kind=schema.get('type')
    valid={'string':isinstance(value,str), 'integer':type(value) is int,
           'number':type(value) in (int,float) and (not isinstance(value,float) or math.isfinite(value)),
           'boolean':type(value) is bool,'array':isinstance(value,list),'object':isinstance(value,dict)}
    if kind not in valid or not valid[kind]:raise ValueError(path+' violates '+str(kind))
    if kind=='array' and 'items' in schema:
        for i,v in enumerate(value):_validate(v,schema['items'],f'{path}[{i}]')
    if kind=='object':
        if any(not isinstance(k,str) for k in value):raise ValueError('object keys must be strings')
        props=schema.get('properties',{})
        if any(k not in value for k in schema.get('required',[])):raise ValueError('missing required argument')
        extra=set(value)-set(props)
        additional=schema.get('additionalProperties',True)
        if extra and additional is False:raise ValueError('unexpected argument')
        for k,v in value.items():
            if k in props:_validate(v,props[k],path+'.'+k)
            elif isinstance(additional,dict):_validate(v,additional,path+'.'+k)

def checked_call(name,arguments):
    try:
        if not isinstance(name,str):raise ValueError('tool name must be string')
        if isinstance(arguments,str):arguments=json.loads(arguments or '{}')
        catalog=tools.catalog()
        if name not in catalog:raise ValueError('unknown tool')
        schema=dict(catalog[name].parameters,type='object',additionalProperties=False)
        _validate(arguments,schema)
        return tools.call_tool(name,arguments)
    except Exception as exc:
        return {'error':f'{type(exc).__name__}: {exc}'}

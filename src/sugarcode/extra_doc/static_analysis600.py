"""Row600 Static Analysis - Finds bugs without running.

Bounded Python AST diagnostic for duplicate constant dict keys and statements
following unconditional return/raise/break/continue in the same lexical block.
No source execution, import resolution, control-flow/data-flow proof, general
bug discovery or security assurance. Findings can be intentional; review them.
"""
import ast


def analyze_source(source):
    """Exact str1..16384 chars; AST<=4096 nodes; parser errors are ValueError.
    Return sorted (line, column, diagnostic_code) findings, no source text.
    """
    if type(source) is not str:
        raise TypeError('exact source string required')
    if not 1<=len(source)<=16384:
        raise ValueError('source length outside declared range')
    try:
        tree=ast.parse(source)
    except (SyntaxError,RecursionError,MemoryError) as exc:
        raise ValueError('source cannot be parsed within limits') from exc
    nodes=list(ast.walk(tree))
    if len(nodes)>4096:
        raise ValueError('AST node cap exceeded')
    findings=[]
    for node in nodes:
        if isinstance(node,ast.Dict):
            seen=set()
            for key in node.keys:
                if isinstance(key,ast.Constant) and type(key.value) in (str,int,float,bool,type(None)):
                    if key.value in seen:
                        findings.append((key.lineno,key.col_offset,'duplicate_constant_dict_key'))
                    seen.add(key.value)
        for _,value in ast.iter_fields(node):
            if type(value) is list and value and all(isinstance(x,ast.stmt) for x in value):
                terminated=False
                for statement in value:
                    if terminated:
                        findings.append((statement.lineno,statement.col_offset,'after_unconditional_terminator'))
                    if isinstance(statement,(ast.Return,ast.Raise,ast.Break,ast.Continue)):
                        terminated=True
    return {'findings':sorted(set(findings)),'node_count':len(nodes)}

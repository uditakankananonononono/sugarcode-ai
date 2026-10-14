import ast
import pytest
from sugarcode.extra_doc.static_analysis600 import analyze_source as run


def test_hand_literal_duplicate_keys_and_dead_statements():
    src="def f():\n    x={'a':1, 'a':2}\n    return x\n    print('never')\n"
    result=run(src)
    assert result['findings']==[(2,14,'duplicate_constant_dict_key'),(4,4,'after_unconditional_terminator')]
    assert result['node_count']==len(list(ast.walk(ast.parse(src))))


def test_no_execution_imports_calls_and_conditional_return_not_terminator():
    src="import no_such_package\nraise RuntimeError('not executed')\nprint('not executed')\n"
    assert run(src)['findings']==[(3,0,'after_unconditional_terminator')]
    assert run('def f(x):\n    if x:\n        return 1\n    return 2\n')['findings']==[]


@pytest.mark.parametrize('terminator',['return','raise RuntimeError()'])
def test_function_block_terminators(terminator):
    assert run('def f():\n    '+terminator+'\n    x=1\n')['findings']==[(3,4,'after_unconditional_terminator')]


@pytest.mark.parametrize('terminator',['break','continue'])
def test_loop_block_terminators(terminator):
    assert run('while True:\n    '+terminator+'\n    x=1\n')['findings']==[(3,4,'after_unconditional_terminator')]


def test_key_equality_python_semantics_and_per_dict_scope():
    assert run('x={1:1, True:2, 1.0:3, None:4, None:5}')['findings']==[(1,8,'duplicate_constant_dict_key'),(1,16,'duplicate_constant_dict_key'),(1,31,'duplicate_constant_dict_key')]
    assert run("a={'k':1};b={'k':2}")['findings']==[]
    assert run("x={unknown:1,unknown:2,**other}")['findings']==[]
    assert run("x={b'a':1,b'a':2}")['findings']==[]


@pytest.mark.parametrize('bad',[None,True,1,1.0,b'x',[],{}])
def test_source_type(bad):
    with pytest.raises(TypeError,match='^exact source string required$'):run(bad)


@pytest.mark.parametrize('n',[0,16385])
def test_source_caps_before_parse(n):
    with pytest.raises(ValueError,match='^source length outside declared range$'):run('!'*n)


@pytest.mark.parametrize('bad',['def :','('*300,'x='])
def test_parse_refusal(bad):
    with pytest.raises(ValueError,match='^source cannot be parsed within limits$'):run(bad)


def test_source_endpoints_and_ast_node_cap():
    assert run('1')['findings']==[]
    assert run('#'+'x'*16383)=={'findings':[],'node_count':1}
    with pytest.raises(ValueError,match='^AST node cap exceeded$'):run(';'.join('x=1' for _ in range(1100)))


def test_each_terminator_following_all_statements_and_nested_blocks():
    src='def f():\n    return\n    x=1\n    y=2\ndef g():\n    x=1\n'
    assert run(src)['findings']==[(3,4,'after_unconditional_terminator'),(4,4,'after_unconditional_terminator')]

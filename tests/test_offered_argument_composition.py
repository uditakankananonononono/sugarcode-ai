"""Independent offered-name and declared-type refusals on the combined tree."""
import json
from sugarcode.llm.agent import _run
from sugarcode.llm.tools import catalog


class Client:
    supports_tools = True
    def __init__(self, arguments):
        self.arguments = arguments
        self.step = 0
        self.results = []
    def chat(self, messages, tools=None):
        self.step += 1
        if self.step == 1:
            return {'tool_calls': [{'id': '1', 'function': {
                'name': 'acmg_bayesian__classify_points',
                'arguments': json.dumps(self.arguments)}}]}
        self.results = [m for m in messages if m['role'] == 'tool']
        return {'content': 'done'}


def test_offered_invalid_argument_and_unoffered_valid_argument_refuse(monkeypatch):
    tool = catalog()['acmg_bayesian__classify_points']
    import sugarcode.modules.acmg_bayesian as module
    dispatched = []
    monkeypatch.setattr(module, 'classify_points', lambda **kw: dispatched.append(kw) or 'called')
    offered_bad = Client({'points': True})
    _, trace = _run(offered_bad, 'question', [tool], 2)
    assert not dispatched and trace[0]['ok'] is False
    assert 'invalid argument points' in offered_bad.results[0]['content']
    unoffered_valid = Client({'points': 1})
    _, trace = _run(unoffered_valid, 'question', [], 2)
    assert not dispatched and trace[0]['ok'] is False
    assert 'not offered' in unoffered_valid.results[0]['content']
    offered_valid = Client({'points': 1})
    _, trace = _run(offered_valid, 'question', [tool], 2)
    assert dispatched == [{'points': 1}] and trace[0]['ok'] is True

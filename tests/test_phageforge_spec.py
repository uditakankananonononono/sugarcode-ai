from sugarcode.modules.phageforge import *
def test_budget(): assert payload_budget('T7',{'cas':3,'guides':.5})['fits']
def test_kill(): assert kill_curve(10)['surviving_fraction'] < kill_curve(.1)['surviving_fraction']
def test_resistance(): assert kill_curve(10,resistant_fraction=.2)['surviving_fraction'] >= .2
def test_escape(): assert escape_risk(2)['escape_probability'] < escape_risk(1)['escape_probability']
def test_coverage(): assert cocktail_coverage({'p1':['a','b'],'p2':['b']})['redundant_hosts']==['b']
def test_invalid():
 try: payload_budget('bad',{})
 except ValueError: return
 assert False

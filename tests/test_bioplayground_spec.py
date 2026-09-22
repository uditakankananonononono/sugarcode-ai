from sugarcode.modules.bioplayground import *
def test_legacy_seeded(): assert run_sandbox(seed=2)==run_sandbox(seed=2)
def test_diversity(): assert diversity_metrics([.5,.5])['heterozygosity']>.4
def test_environment(): assert len(environment_sweep([{'fitness':[1,.9]},{'fitness':[.9,1]}],pop_size=50,generations=10,n_alleles=2,bottleneck_size=5)['runs'])==2
def test_directed(): assert directed_evolution(5,[{'id':'a','score':0},{'id':'b','score':1}])['history']
def test_ecology(): assert len(ecological_competition([.2,.2],[1,1],[[1,.5],[.5,1]],10)['trajectory'])==11
def test_report(): assert 'no learned evolutionary model' in playground_report([{'fitness':[1,.9]},{'fitness':[.9,1]}])['model_status']

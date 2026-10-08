import copy,json,pytest
from sugarcode.report.notebook import new_notebook,validate_notebook

def test_actual_schema_and_serialization():
 from sugarcode.report.notebook_checked import normalize,validate,serialize
 source=new_notebook([{'cell_type':'code','source':'print(1)'},{'cell_type':'markdown','source':'text'}])
 assert validate(source)
 repaired=normalize(source);assert not validate(repaired) and 'id' not in source['cells'][0]
 assert json.loads(serialize(repaired))==repaired

def test_invalid_counts_outputs_duplicate_ids():
 from sugarcode.report.notebook_checked import normalize,validate,serialize
 n=normalize(new_notebook([{'cell_type':'code','source':'print(1)'}]))
 for field,value in [('execution_count','wrong'),('execution_count',True),('outputs',[{'output_type':'made_up'}])]:
  bad=copy.deepcopy(n);bad['cells'][0][field]=value;assert validate(bad)
  with pytest.raises(ValueError):serialize(bad)
 n['cells'].append(copy.deepcopy(n['cells'][0]));assert validate(n)

def test_no_coercion_or_execution():
 from sugarcode.report.notebook_checked import normalize,validate
 n=new_notebook([{'cell_type':'code','source':'raise RuntimeError("must not execute")'}])
 n['cells'][0]['execution_count']='bad'
 with pytest.raises(ValueError):normalize(n)

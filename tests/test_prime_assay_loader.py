"""Synthetic validation cases; no assay data redistributed by these tests."""
import csv
import hashlib
from pathlib import Path
import pytest


def loader():
    from sugarcode.modules.prime_design.assay_data import load_pridict2_csv
    return load_pridict2_csv


def write_table(tmp_path, rows):
    p = tmp_path/'table.csv'
    with p.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    return p


def row(seq='seq_0', group='0', hek=(.2,.7,.1), k562=(0,0,0)):
    d = dict(seq_id=seq, grp_id=group, wide_initial_target='ACGTACGT',
             wide_mutated_target='ACGTTCGT', PBSlength=10, RTlength=14,
             PBSlocation='[0, 4]', RT_initial_location='[4, 8]',
             RT_mutated_location='[4, 8]', protospacerlocation_only_initial='[0, 7]',
             Correction_Type='Replacement', Correction_Length=1)
    for cell,values in [('HEK',hek),('K562',k562)]:
        for kind,value in zip(('edited','unedited','unintended'),values):
            d[cell+'average'+kind+'_clamped']=value
    return d


def test_zero_triple_preserved_as_missing(tmp_path):
    p=write_table(tmp_path,[row()]);r=loader()(p, verify_source=False)[0]
    assert r['outcomes']['HEK'] == (.2,.7,.1)
    assert r['outcomes']['K562'] is None
    assert r['grp_id']=='0' and r['wide_initial_target']=='ACGTACGT'
    assert r['pbs_location']==(0,4)


def test_source_hash_required_by_default(tmp_path):
    p=write_table(tmp_path,[row()])
    with pytest.raises(ValueError, match='SHA256'):
        loader()(p)


@pytest.mark.parametrize('updates', [
    {'HEKaverageedited_clamped':float('nan')},
    {'HEKaverageedited_clamped':-.1},
    {'HEKaverageedited_clamped':.9},
    {'wide_initial_target':'ACGTNACGT'},
    {'PBSlocation':'__import__("os").system("true")'},
    {'PBSlocation':'[4, 20]'}, {'RTlength':0},
])
def test_bad_table_rejected(tmp_path, updates):
    p=write_table(tmp_path,[dict(row(),**updates)])
    with pytest.raises(ValueError):loader()(p, verify_source=False)


def test_duplicate_ids_rejected(tmp_path):
    p=write_table(tmp_path,[row(),row()])
    with pytest.raises(ValueError):loader()(p,verify_source=False)


def test_missing_schema_rejected(tmp_path):
    p=write_table(tmp_path,[{'seq_id':'x'}])
    with pytest.raises(ValueError):loader()(p,verify_source=False)


def workbook_row(group='0', initial='ACGTACGT', fold='1'):
    return dict(group=group, wide_initial_target=initial,
                wide_mutated_target='ACGTTCGT', PBS='ACGTACGTAC',
                RTT='ACGTACGTACGTAC', spacer='ACGT'*5,
                Editor_Variant='PE2-NGG', Name='synthetic', test_split_hek=fold)


def join_table(tmp_path, monkeypatch, csv_rows, workbook_rows):
    from sugarcode.modules.prime_design import assay_data as a
    p=write_table(tmp_path,csv_rows)
    monkeypatch.setattr(a,'_workbook_rows', lambda _: iter(workbook_rows))
    return a.load_pridict2_assay(p,tmp_path/'unused.xlsx',verify_source=False)


def test_join_keeps_distinct_cell_folds_and_source_sequences(tmp_path, monkeypatch):
    a=row(k562=(.1,.8,.1));b=workbook_row();b['test_split_k562']='3'
    result=join_table(tmp_path,monkeypatch,[a],[b]);r=result['records'][0]
    assert r['test_folds']=={'HEK':1,'K562':3}
    assert r['pbs']=='ACGTACGTAC' and r['spacer']=='ACGT'*5
    assert result['source_integrity_verified'] is False
    assert 'UNVERIFIED' in result['reuse_status']


@pytest.mark.parametrize('change',[
    {'group':'wrong'}, {'wide_initial_target':'TTTTTTTT'},
    {'PBS':'ACGT'}, {'spacer':'ACGT'}, {'Editor_Variant':'PE3'},
    {'test_split_hek':'5'}, {'test_split_k562':'1'}, {'test_split_hek':''},
])
def test_bad_join_metadata_rejected(tmp_path,monkeypatch,change):
    with pytest.raises(ValueError):
        join_table(tmp_path,monkeypatch,[row()],[dict(workbook_row(),**change)])


def test_group_fold_leakage_rejected(tmp_path,monkeypatch):
    with pytest.raises(ValueError, match='leakage'):
        join_table(tmp_path,monkeypatch,[row(),row('seq_1')],
                   [workbook_row(),workbook_row(fold='2')])


@pytest.mark.parametrize('n', [0,2])
def test_workbook_row_count_must_match(tmp_path,monkeypatch,n):
    with pytest.raises(ValueError):
        join_table(tmp_path,monkeypatch,[row()],[workbook_row()]*n)

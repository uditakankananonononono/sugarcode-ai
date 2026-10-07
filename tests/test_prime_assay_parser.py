"""Synthetic OOXML only; no source assay cells redistributed."""
from zipfile import ZipFile
import pytest
from sugarcode.modules.prime_design.assay_data import _workbook_rows, load_pridict2_csv
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def book(tmp_path, cells, strings=('one','two'), header=None):
    p=tmp_path/'synthetic.xlsx'
    if header is None:
        header='<c r="A1" t="inlineStr"><is><t>field</t></is></c>'
    with ZipFile(p,'w') as z:
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{NS}"><sheets><sheet name="final_df_with_splits"/></sheets></workbook>')
        z.writestr('xl/sharedStrings.xml',f'<sst xmlns="{NS}">'+''.join(f'<si><t>{s}</t></si>' for s in strings)+'</sst>')
        z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{NS}"><sheetData><row r="1">{header}</row><row r="2">{cells}</row></sheetData></worksheet>')
    return p


def test_values_without_formula_execution(tmp_path):
    p=book(tmp_path,'<c r="A2" t="s"><v>1</v></c>')
    assert list(_workbook_rows(p))==[{'field':'two'}]


@pytest.mark.parametrize('cell',[
    '<c r="A2" t="s"><v>-1</v></c>',
    '<c r="A2" t="s"><v>99</v></c>',
    '<c r="A2" t="s"><v>bad</v></c>',
    '<c r="A2"><f>1+1</f><v>2</v></c>',
    '<c r="A2"><v>1</v></c><c r="A2"><v>2</v></c>',
    '<c r="B2"><v>1</v></c>',
])
def test_invalid_workbook_cells_fail_closed(tmp_path,cell):
    with pytest.raises(ValueError):list(_workbook_rows(book(tmp_path,cell)))


def test_duplicate_workbook_headers_rejected(tmp_path):
    header='<c r="A1" t="inlineStr"><is><t>field</t></is></c><c r="B1" t="inlineStr"><is><t>field</t></is></c>'
    with pytest.raises(ValueError):list(_workbook_rows(book(tmp_path,'<c r="A2"><v>1</v></c>',header=header)))


def test_duplicate_csv_header_rejected(tmp_path):
    from sugarcode.modules.prime_design.assay_data import _REQUIRED
    keys=sorted(_REQUIRED)+['seq_id'];p=tmp_path/'dup.csv'
    p.write_text(','.join(keys)+'\n'+','.join(['x']*len(keys))+'\n')
    with pytest.raises(ValueError,match='duplicate'):
        load_pridict2_csv(p,verify_source=False)


@pytest.mark.parametrize('flag',[None,0,1,'false'])
def test_integrity_flag_requires_explicit_bool(tmp_path,flag):
    with pytest.raises(ValueError,match='boolean'):
        load_pridict2_csv(tmp_path/'nonexistent.csv',verify_source=flag)


def test_optional_workbook_error_preserved_as_missing(tmp_path):
    p=book(tmp_path,'<c r="A2" t="e"><v>#VALUE!</v></c>')
    assert list(_workbook_rows(p))==[{'field':None}]

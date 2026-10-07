"""Offline, source-pinned PRIDICT2 assay ingestion. No fetch, training or weights.

Dataset-specific reuse terms have not been verified. This module supplies no
assay bytes. A caller must obtain appropriate permission before fitting/sharing.
All-zero processed outcome triples are missing, never measured zero efficiency.
"""
from pathlib import Path
import ast
import csv
import hashlib
import math
import xml.etree.ElementTree as ET
from zipfile import ZipFile

CSV_SHA256 = 'fcffe27e4d3e4b814129ecc68a7d64afb4547adde2f0f052a3db5b77ba476200'
WORKBOOK_SHA256 = '4d0ab0dc1d8d914f1960328a19fbc42640c9aaa5304c16650999c9426698ecdc'
SOURCE_COMMITS = {'csv': 'c133c35e205062e766bf515d1766169167e993b9',
                  'workbook': 'c024f806a9590b1395b85a337276629caac134a5'}
CELLS = ('HEK', 'K562')
OUTCOME_CLASSES = ('edited', 'unedited', 'unintended')
_REQUIRED = {'seq_id', 'grp_id', 'wide_initial_target', 'wide_mutated_target',
             'PBSlength', 'RTlength', 'PBSlocation', 'RT_initial_location',
             'RT_mutated_location', 'protospacerlocation_only_initial',
             'Correction_Type', 'Correction_Length'} | {
                 f'{cell}average{kind}_clamped' for cell in CELLS for kind in OUTCOME_CLASSES}
_NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def _verify(path, digest):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    if h.hexdigest() != digest:
        raise ValueError('SHA256 mismatch: artifact differs from pinned assay source')


def _dna(value):
    if not isinstance(value, str) or not value or set(value)-set('ACGT'):
        raise ValueError('assay sequence must be nonempty unambiguous uppercase DNA')
    return value


def _positive_integer(value):
    try:
        x = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError('positive integer required') from exc
    if not math.isfinite(x) or x < 1 or not x.is_integer():
        raise ValueError('positive integer required')
    return int(x)


def _location(value, sequence):
    try:
        result = ast.literal_eval(value)
    except (ValueError, SyntaxError, TypeError) as exc:
        raise ValueError('invalid assay location literal') from exc
    if (not isinstance(result, (list, tuple)) or len(result) != 2 or
            any(type(v) is not int for v in result) or
            not 0 <= result[0] < result[1] <= len(sequence)):
        raise ValueError('assay location outside sequence boundaries')
    return tuple(result)


def _outcome(row, cell):
    try:
        values = tuple(float(row[f'{cell}average{kind}_clamped']) for kind in OUTCOME_CLASSES)
    except (ValueError, TypeError) as exc:
        raise ValueError('invalid assay outcome') from exc
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in values):
        raise ValueError('assay outcome must be finite and bounded')
    if all(v == 0 for v in values):
        return None
    if not math.isclose(sum(values), 1, rel_tol=0, abs_tol=1e-7):
        raise ValueError('nonmissing assay outcome must sum to one; never renormalized')
    return values


def load_pridict2_csv(path, *, verify_source=True):
    """Return checked processed records. verify_source=False is for synthetic tests.

    Location conventions are retained as source indices, not silently translated
    into SugarCode's design coordinate system. Full pegRNA strings and folds need
    the supplementary workbook. No missing outcome is imputed or normalized.
    """
    if type(verify_source) is not bool:
        raise ValueError('verify_source must be boolean')
    if verify_source:
        _verify(path, CSV_SHA256)
    records, seen = [], set()
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or ()
        if len(set(fields)) != len(fields):
            raise ValueError('duplicate CSV headers')
        if not _REQUIRED <= set(fields):
            raise ValueError('missing required PRIDICT2 columns')
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('CSV row width differs from schema')
            identity, group = row['seq_id'], row['grp_id']
            if not identity or identity in seen or not group:
                raise ValueError('empty or duplicate identity / empty group')
            seen.add(identity)
            initial = _dna(row['wide_initial_target'])
            mutated = _dna(row['wide_mutated_target'])
            if row['Correction_Type'] not in ('Replacement', 'Insertion', 'Deletion'):
                raise ValueError('unsupported assay correction type')
            records.append({
                'seq_id': identity, 'grp_id': group,
                'wide_initial_target': initial, 'wide_mutated_target': mutated,
                'pbs_length': _positive_integer(row['PBSlength']),
                'rtt_length': _positive_integer(row['RTlength']),
                'correction_type': row['Correction_Type'],
                'correction_length': _positive_integer(row['Correction_Length']),
                'pbs_location': _location(row['PBSlocation'], initial),
                'rt_initial_location': _location(row['RT_initial_location'], initial),
                'rt_mutated_location': _location(row['RT_mutated_location'], mutated),
                'protospacer_location_source': _location(row['protospacerlocation_only_initial'], initial),
                'outcomes': {cell: _outcome(row, cell) for cell in CELLS},
            })
    if not records:
        raise ValueError('empty assay table')
    return records


def _workbook_rows(path):
    """Read values only; never execute formulas, macros, links or pickle payloads."""
    with ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist()) > 300_000_000:
            raise ValueError('workbook exceeds decompressed resource limit')
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = workbook.findall('s:sheets/s:sheet', _NS)
        if len(sheets) != 1 or sheets[0].get('name') != 'final_df_with_splits':
            raise ValueError('unexpected workbook sheet layout')
        shared = []
        with z.open('xl/sharedStrings.xml') as f:
            for _, element in ET.iterparse(f, events=('end',)):
                if element.tag.endswith('}si'):
                    shared.append(''.join(element.itertext()))
                    element.clear()
        header = None
        with z.open('xl/worksheets/sheet1.xml') as f:
            for _, element in ET.iterparse(f, events=('end',)):
                if not element.tag.endswith('}row'):
                    continue
                values = {}
                for c in element.findall('s:c', _NS):
                    if c.find('s:f', _NS) is not None:
                        raise ValueError('formula cells not accepted as measured assay values')
                    value = c.find('s:v', _NS)
                    text = value.text if value is not None else ''.join(c.itertext())
                    if c.get('t') == 'e':
                        text = None  # Preserve spreadsheet errors as missing, never literal labels.
                    if c.get('t') == 's':
                        try:
                            index = int(text)
                        except (ValueError, TypeError) as exc:
                            raise ValueError('invalid workbook shared-string index') from exc
                        if not 0 <= index < len(shared):
                            raise ValueError('workbook shared-string index outside table')
                        text = shared[index]
                    column = ''.join(filter(str.isalpha, c.get('r', '')))
                    if not column or column in values:
                        raise ValueError('invalid or duplicate workbook cell reference')
                    values[column] = text
                if header is None:
                    if not values or any(v is None for v in values.values()) or len(set(values.values())) != len(values):
                        raise ValueError('empty or duplicate workbook headers')
                    header = values
                else:
                    if not set(values) <= set(header):
                        raise ValueError('workbook value outside header schema')
                    yield {header[k]: v for k, v in values.items() if k in header}
                element.clear()


def load_pridict2_assay(csv_path, workbook_path, *, verify_source=True):
    """Join pinned sources by checked row identity/context, preserving cell folds.

    This is a data loader, not a grant to fit or redistribute. No model is trained.
    Missing outcomes have None folds; nonmissing groups have one test fold per
    cell. HEK and K562 assignments are retained independently.
    """
    records = load_pridict2_csv(csv_path, verify_source=verify_source)
    if verify_source:
        _verify(workbook_path, WORKBOOK_SHA256)
    groups = {cell: {} for cell in CELLS}
    count = 0
    for i, row in enumerate(_workbook_rows(workbook_path)):
        if i >= len(records):
            raise ValueError('workbook has extra rows')
        record = records[i]
        for key in ('wide_initial_target', 'wide_mutated_target'):
            if row.get(key) != record[key]:
                raise ValueError('workbook/CSV row context mismatch')
        if row.get('group') != record['grp_id']:
            raise ValueError('workbook/CSV group mismatch')
        pbs, rtt, spacer = (_dna(row.get(k)) for k in ('PBS', 'RTT', 'spacer'))
        if len(pbs) != record['pbs_length'] or len(rtt) != record['rtt_length'] or len(spacer) != 20:
            raise ValueError('workbook sequence lengths disagree with assay metadata')
        if row.get('Editor_Variant') != 'PE2-NGG':
            raise ValueError('unexpected assay editor context')
        folds = {}
        for cell in CELLS:
            value = row.get('test_split_'+cell.lower())
            missing = record['outcomes'][cell] is None
            if missing:
                if value not in (None, ''):
                    raise ValueError('missing assay outcome has nonmissing test fold')
                folds[cell] = None
            else:
                if value not in ('0', '1', '2', '3', '4'):
                    raise ValueError('nonmissing assay outcome needs fold 0-4')
                fold = int(value)
                previous = groups[cell].setdefault(record['grp_id'], fold)
                if previous != fold:
                    raise ValueError('group leakage across cell-specific test folds')
                folds[cell] = fold
        record.update(pbs=pbs, rt_template=rtt, spacer=spacer,
                      editor='PE2-NGG', test_folds=folds, source_name=row.get('Name'))
        count += 1
    if count != len(records):
        raise ValueError('workbook missing rows')
    return {'records': records, 'outcome_classes': OUTCOME_CLASSES,
            'source_commits': dict(SOURCE_COMMITS),
            'source_integrity_verified': verify_source,
            'reuse_status': 'DATA_REUSE_UNVERIFIED: no fitting or redistribution approval',
            'model_status': 'Loader only; no model fitted, no clinical/spec validation'}


def plan_pridict2_partition(assay, cell, test_fold, *, validation_fraction=.1,
                            seed=42):
    """Plan an additional group-safe validation holdout, without any fitting.

    Original cell-specific test folds are preserved. Validation groups are
    selected from non-test groups by a stable seeded SHA256 ordering, not the
    original author's training/validation algorithm. validation_fraction applies
    to remaining groups, not rows; rounding can change realized row fraction.
    Empty/single-group training pools cannot form both train and validation and
    are reported, never silently split a group. The reuse gate stays closed.
    """
    from collections.abc import Mapping
    if cell not in CELLS or type(test_fold) is not int or not 0 <= test_fold <= 4:
        raise ValueError('cell must be HEK/K562 and test_fold an integer 0-4')
    if (isinstance(validation_fraction, bool) or
            not isinstance(validation_fraction, (int, float)) or
            not math.isfinite(validation_fraction) or not 0 < validation_fraction < 1):
        raise ValueError('validation_fraction must be finite and strictly between zero and one')
    if type(seed) is not int:
        raise ValueError('seed must be integer')
    if not isinstance(assay, Mapping) or not isinstance(assay.get('records'), list):
        raise ValueError('assay must contain records list')
    groups, missing, seen = {}, [], set()
    for i, row in enumerate(assay['records']):
        if not isinstance(row, Mapping):
            raise ValueError('record must be mapping')
        identity, group = row.get('seq_id'), row.get('grp_id')
        if not isinstance(identity, str) or not identity or identity in seen or not isinstance(group, str) or not group:
            raise ValueError('record identity/group invalid or duplicated')
        seen.add(identity)
        outcomes, folds = row.get('outcomes'), row.get('test_folds')
        if not isinstance(outcomes, Mapping) or cell not in outcomes or not isinstance(folds, Mapping) or cell not in folds:
            raise ValueError('record requires selected cell outcome and fold')
        value, fold = outcomes[cell], folds[cell]
        if value is None:
            if fold is not None:
                raise ValueError('missing outcome requires missing fold')
            missing.append(i)
            continue
        if (not isinstance(value, (tuple, list)) or len(value) != 3 or
                any(isinstance(v, bool) or not isinstance(v, (int, float)) or
                    not math.isfinite(v) or not 0 <= v <= 1 for v in value) or
                not math.isclose(sum(value), 1, rel_tol=0, abs_tol=1e-7)):
            raise ValueError('selected cell outcomes invalid')
        if type(fold) is not int or not 0 <= fold <= 4:
            raise ValueError('nonmissing outcome requires integer fold 0-4')
        if group not in groups:
            groups[group] = {'fold': fold, 'indices': []}
        if groups[group]['fold'] != fold:
            raise ValueError('group leakage across folds')
        groups[group]['indices'].append(i)
    available = [g for g in groups if groups[g]['fold'] != test_fold]
    available.sort(key=lambda g: (hashlib.sha256(f'{seed}:{g}'.encode()).digest(), g))
    count = min(len(available)-1, max(1, math.floor(len(available)*validation_fraction+.5))) if len(available) >= 2 else 0
    validation_groups = set(available[:count])
    result = {'train': [], 'validation': [], 'test': [], 'excluded_missing': missing}
    for group, info in groups.items():
        destination = ('test' if info['fold'] == test_fold else
                       'validation' if group in validation_groups else 'train')
        result[destination].extend(info['indices'])
    for key in ('train', 'validation', 'test'):
        result[key].sort()
    result.update(cell=cell, test_fold=test_fold, seed=seed,
                  validation_fraction_requested=validation_fraction,
                  validation_group_count=count,
                  non_test_group_count=len(available),
                  partition_status=('ready' if len(available) >= 2 else 'insufficient groups for train and validation'),
                  fitting_permitted=False,
                  reuse_status='DATA_REUSE_UNVERIFIED: fitting/redistribution gate CLOSED',
                  method='original cell test folds; stable SHA256 group validation holdout')
    return result


def evaluate_outcome_predictions(assay, predictions, cell, indices):
    """Distribution error arithmetic, not fitting or clinical model validation.

    Intended MAE/RMSE and mean total variation are measured against provided
    fractions. Squared distribution error sums across classes before averaging.
    No count likelihood, confidence intervals or calibration claim without
    denominators/replicate analysis. Caller supplies an explicit evaluation set;
    this function cannot attest it is held out. Data reuse gate is unchanged.
    """
    from collections.abc import Mapping
    if cell not in CELLS or not isinstance(assay, Mapping) or not isinstance(assay.get('records'), list):
        raise ValueError('assay records and supported cell required')
    if not isinstance(predictions, Mapping) or not isinstance(indices, (list, tuple)):
        raise ValueError('predictions mapping and explicit indices required')
    rows = assay['records']
    if any(type(i) is not int or not 0 <= i < len(rows) for i in indices) or len(set(indices)) != len(indices):
        raise ValueError('indices must be distinct valid integers')

    def distribution(value):
        if (not isinstance(value, (tuple, list)) or len(value) != 3 or
                any(isinstance(v, bool) or not isinstance(v, (int, float)) or
                    not math.isfinite(v) or not 0 <= v <= 1 for v in value) or
                not math.isclose(sum(value), 1, rel_tol=0, abs_tol=1e-7)):
            raise ValueError('distribution must be finite bounded normalized triple')
        return tuple(value)

    observed, missing, seen = {}, 0, set()
    for i in indices:
        row = rows[i]
        if not isinstance(row, Mapping) or not isinstance(row.get('outcomes'), Mapping) or cell not in row['outcomes']:
            raise ValueError('invalid selected record')
        identity = row.get('seq_id')
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError('selected identities must be distinct nonempty strings')
        seen.add(identity)
        if row['outcomes'][cell] is None:
            missing += 1
        else:
            observed[identity] = distribution(row['outcomes'][cell])
    if set(predictions) != set(observed):
        raise ValueError('prediction IDs must exactly match observed selected labels')
    abs_errors, square_errors, tv_errors, distribution_errors = [], [], [], []
    for identity, actual in observed.items():
        predicted = distribution(predictions[identity])
        differences = [p-a for p, a in zip(predicted, actual)]
        abs_errors.append(abs(differences[0]))
        square_errors.append(differences[0]**2)
        tv_errors.append(sum(abs(x) for x in differences)/2)
        distribution_errors.append(sum(x*x for x in differences))
    n = len(observed)
    return {'n_scored': n, 'n_missing': missing,
            'intended_mae': math.fsum(abs_errors)/n if n else None,
            'intended_rmse': math.sqrt(math.fsum(square_errors)/n) if n else None,
            'mean_total_variation': math.fsum(tv_errors)/n if n else None,
            'mean_squared_distribution_error': math.fsum(distribution_errors)/n if n else None,
            'status': 'Error arithmetic only; held-out status unverified, not clinical validation',
            'reuse_status': 'DATA_REUSE_UNVERIFIED: fitting/redistribution gate CLOSED'}

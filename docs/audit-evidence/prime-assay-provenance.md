# PRIDICT2 loader source integrity and reuse gate

Checked 2026-10-07. No assay records redistributed; runtime takes local files.

- Processed CSV: https://raw.githubusercontent.com/uzh-dqbm-cmi/PRIDICT2/main/dataset/proc_v2/data_23k_v1.csv
  Source commit https://github.com/uzh-dqbm-cmi/PRIDICT2/commit/c133c35e205062e766bf515d1766169167e993b9
  SHA256 fcffe27e4d3e4b814129ecc68a7d64afb4547adde2f0f052a3db5b77ba476200
- Workbook: https://raw.githubusercontent.com/Schwank-Lab/epridict/supplementary_files/SupplFile1_Library_Diverse_Editing_Results_with_test_splits.xlsx
  Source commit https://github.com/Schwank-Lab/epridict/commit/c024f806a9590b1395b85a337276629caac134a5
  SHA256 4d0ab0dc1d8d914f1960328a19fbc42640c9aaa5304c16650999c9426698ecdc
- Notebook: https://raw.githubusercontent.com/uzh-dqbm-cmi/PRIDICT2/main/notebooks/train_eval/process_23kdataset_v1.ipynb
  Inspected as text; it explicitly excludes separate cell-specific missing rows
  and checks grouped folds for train/validation/test overlap.
- Primary paper: https://www.nature.com/articles/s41587-024-02268-2
  Data availability: measured editing rates in Supplementary Tables 2, 7, 8, 12;
  sequencing SRA PRJNA1025026. Rights and permissions: Springer Nature or its
  licensor holds exclusive article rights. No clear dataset-specific reuse
  permission verified. Public downloadability is not a data reuse license.
- Code LICENSE: https://raw.githubusercontent.com/uzh-dqbm-cmi/PRIDICT2/main/LICENSE
  MIT; do not substitute it for unverified dataset terms.

Loader validates all local rows against pinned hashes by default; bypass exists
only for synthetic testing and marks integrity unverified. No fetch helper,
training entry point, labels copied to fixtures, or data bundled in package.
The output preserves source index conventions, including protospacer location,
without converting them into design coordinates. It retains three outcome classes
and cell-specific missingness and folds, but does not assert those classes identify
MMR, BER, FEN1, pure indels, reversion or partial readthrough.

Real-source aggregate execution is in prime-assay-real-source-2026-10-07.txt.
Tests are numerical/schema/join validation, not independent assay validation.
Fitting and redistribution wait for actual reuse terms verification.

"""Explicit-import numerical assay partition seed contract.

SCOPED seed preflight; module PARTIAL. Preserves partition arithmetic for valid
Python integer seeds. No fitting, sequence generation, guide design or change
to the existing assay-data reuse gate. Legacy entry points are unchanged.
"""
from . import assay_data
from ...seed_check import check_seed


def plan_pridict2_partition(assay,cell,test_fold,*,validation_fraction=.1,seed=42):
    seed=check_seed(seed)
    return assay_data.plan_pridict2_partition(assay,cell,test_fold,
        validation_fraction=validation_fraction,seed=seed)

import math
import pytest
from sugarcode.modules.crispr_muse import *

CAS12A_SEQ="AAATTTAC"+"G"*23+"C"*10
SP_SEQ="C"*20+"AGG"+"C"*10

def test_bug66_cas12a_five_prime_pam_found():
    c=enumerate_configurations(CAS12A_SEQ,["Cas12a"])
    assert len(c)==1 and c[0]["guide"]=="C"+"G"*22 and c[0]["pam"]=="TTTA" and c[0]["start"]==7 and c[0]["cut_site"]==21

def test_bug66_casx_five_prime_pam_found():
    c=enumerate_configurations("TT"+"TTCA"+"A"*20+"GG",["CasX"])
    assert len(c)==1 and c[0]["guide"]=="A"*20

def test_spcas9_three_prime_pam_unchanged():
    c=enumerate_configurations(SP_SEQ,["SpCas9"])
    assert c==[{"nuclease":"SpCas9","guide":"C"*20,"pam":"AGG","start":0,"end":20,"cut_site":17}]

def test_beta_posterior_closed_form():
    bp=bayesian_posterior(8,2); assert bp["mean"]==pytest.approx(9/12) and bp["std"]==pytest.approx(math.sqrt(27/(144*13)))

def test_repair_distribution_normalized():
    ro=repair_outcomes("ACGT"*10); assert ro["NHEJ"]+ro["MMEJ"]+ro["HDR"]==pytest.approx(1)

def test_clonal_expansion_matches_geometric_selection():
    ce=clonal_expansion({"a":.9,"b":.1},10,{"a":1,"b":2})
    assert ce["b"]==pytest.approx(102.4/102.4+0 if False else 102.4/(102.4+.9),rel=1e-6)

def test_diagnostics_key_counts():
    assert len(guide_diagnostics("ACGTACGTACGTACGTACGT"))==32
    assert len(guide_diagnostics("ACGTACGTACGTACGTACGT",background="ACGT"*10))==35

def test_policy_entropy_uniform_is_ln4():
    assert policy_entropy([[0,0,0,0]])==pytest.approx(math.log(4))

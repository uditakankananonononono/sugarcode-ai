import random
from sugarcode.modules.profile_hmm import build_profile_hmm, forward, forward_local

ALN = ["ACDEFGHIKL", "ACDEFGHIKV", "ACDEYGHIKL", "SCDEFGHIRL", "ACDEFGNIKL"]


def _flank(n, seed):
    r = random.Random(seed)
    return "".join(r.choice("ACDEFGHIKLMNPQRSTVWY") for _ in range(n))


def test_local_is_flank_tolerant_global_is_not():
    m = build_profile_hmm(ALN)
    core = "ACDEFGHIKL"
    wrapped = _flank(60, 1) + core + _flank(60, 2)
    loc_core, loc_wrap = forward_local(m, core)["log_odds_bits"], forward_local(m, wrapped)["log_odds_bits"]
    glo_core, glo_wrap = forward(m, core)["log_odds_bits"], forward(m, wrapped)["log_odds_bits"]
    import math
    # local pays only the flank-length cost: 2*log2(n+1) grows from 6.9 to 14.1 bits
    expected_drop = 2 * math.log2(len(wrapped) + 1) - 2 * math.log2(len(core) + 1)
    assert loc_core - loc_wrap < expected_drop + 2
    assert loc_wrap > 0                      # domain still detected inside the long sequence
    assert glo_wrap < glo_core - 40          # global charges every flank residue to inserts


def test_local_separates_member_from_decoy():
    m = build_profile_hmm(ALN)
    member = _flank(30, 3) + "ACDEFGHIKL" + _flank(30, 4)
    decoy = _flank(70, 5)
    assert forward_local(m, member)["log_odds_bits"] > forward_local(m, decoy)["log_odds_bits"] + 5

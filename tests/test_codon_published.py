"""Drop 12: published codon usage tables (Edinburgh Genome Foundry) with provenance."""
import pytest
from sugarcode.bio import codon
from sugarcode.bio.sequence import STANDARD_CODE


class TestPublishedTables:
    def test_tables_load_and_cover_code(self):
        for name in ["e_coli_316407", "h_sapiens_9606", "s_cerevisiae_4932"]:
            t = codon.load_published_table(name)
            assert len(t) == 64
            assert all("U" not in c for c in t)  # DNA codons

    def test_relative_frequencies_sum_to_one_per_aa(self):
        t = codon.load_published_table("e_coli_316407")
        by_aa = {}
        for c, f in t.items():
            by_aa.setdefault(STANDARD_CODE[c], []).append(f)
        for aa, fs in by_aa.items():
            assert abs(sum(fs) - 1.0) < 0.02, f"{aa} sums to {sum(fs)}"

    def test_unknown_species_raises(self):
        with pytest.raises(ValueError):
            codon.load_published_table("n_mysterium")

    def test_human_arg_tie_honest(self):
        """Provenance cross-validation: the published table has an exact AGA/AGG
        tie for Arg (0.21 each); the legacy memory table broke the tie toward
        AGA. Documented in PROVENANCE.md - immaterial, but stated."""
        pub = codon.HUMAN_PUBLISHED
        assert pub["AGG"] == pub["AGA"]
        assert codon.H_SAPIENS_LEGACY["AGA"] > codon.H_SAPIENS_LEGACY["AGG"]

    def test_ecoli_top_codons_match_legacy(self):
        """E. coli legacy memory table agreed 21/21 on top codons - lock that."""
        def tops(table):
            by_aa = {}
            for c, f in table.items():
                aa = STANDARD_CODE[c]
                by_aa.setdefault(aa, []).append((f, c))
            return {aa: max(lst)[1] for aa, lst in by_aa.items()}
        assert tops(codon.ECOLI_PUBLISHED) == tops(codon.ECOLI_LEGACY)

    def test_max_frequency_design_gives_cai_one(self):
        t = codon.ECOLI_PUBLISHED
        # Met/Trp are excluded from CAI by convention (single-codon families)
        assert codon.cai("ATGATGATG", t) == 0.0
        w = codon.relative_adaptiveness(t)
        top_leu = max(["TTA", "TTG", "CTT", "CTC", "CTA", "CTG"], key=lambda c: w[c])
        assert codon.cai(top_leu * 3, t) == pytest.approx(1.0)


class TestOptimizeWithPublishedHosts:
    def test_new_hosts_registered(self):
        for h in ["ecoli", "ecoli_published", "human", "s_cerevisiae", "yeast",
                  "ecoli_legacy", "h_sapiens_legacy"]:
            assert h in codon.HOST_TABLES

    def test_optimize_yeast(self):
        from sugarcode.modules.codon_opt import optimize
        # wide band: native AT-rich yeast GC is fine, CAI improves
        r = optimize("MKTAYIAKQRQISFVK", host="s_cerevisiae", gc_min=0.2, gc_max=0.8)
        assert r["host"] == "s_cerevisiae"
        assert 0 < r["cai_before"] <= r["cai_after"] <= 1.0
        assert len(r["optimized_dna"]) == 3 * 16

    def test_gc_repair_cost_reported_honestly(self):
        from sugarcode.modules.codon_opt import optimize
        # default band forces AT-rich yeast codons toward GC: CAI drops and the
        # output must SAY so rather than silently return a worse sequence
        r = optimize("MKTAYIAKQRQISFVK", host="s_cerevisiae")
        assert r["cai_gc_repair_cost"] > 0.02
        assert r["gc_repair_note"] and "widen the band" in r["gc_repair_note"]

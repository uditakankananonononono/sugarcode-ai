from omega import REGISTRY, SUBNETWORKS, module_slugs
from omega.health import module_health, compute_flux
from omega.search import biological_search


def test_registry_95_modules_9_subnetworks():
    assert len(REGISTRY) == 95
    assert len(SUBNETWORKS) == 9
    assert sum(len(module_slugs(s)) for s in SUBNETWORKS) == 95


def test_every_module_has_summary():
    assert all(len(m.summary) > 20 for m in REGISTRY.values())


def test_health_online_for_built_modules():
    for slug in ["gene_explorer", "crispr_opt", "codon_opt", "prime_design",
                 "deepsplice", "str_scope", "rna_decoder", "promoter_lib",
                 "dark_genome", "virtual_cell", "synbio_studio",
                 "living_computer", "neuro_hub", "omega_stats", "ecosystem",
                 "dna_to_code"]:
        h = module_health(slug)
        assert h["importable"], slug


def test_compute_flux_shape():
    flux = compute_flux()
    assert flux["modules_total"] == 95
    assert flux["modules_online"] >= 16
    assert len(flux["subnetworks"]) == 9


def test_search_finds_crispr():
    r = biological_search("CRISPR guide RNA design off-target")
    slugs = [x["slug"] for x in r["results"]]
    assert "crispr_opt" in slugs

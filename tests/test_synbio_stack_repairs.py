"""Focused mathematical and serialization contracts using local fixtures."""
import pytest
from xml.etree import ElementTree as ET
from sugarcode.modules.synbio_wizard.core import compile_project, run_wizard, codon_metrics, sbml_export


def test_part_budget_refuses_excess_before_result():
    for call in (compile_project, run_wizard):
        with pytest.raises(ValueError, match='part budget'):
            call('vanillin', parts_max=1)
        assert call('vanillin', parts_max=6)


def test_gc_windows_slide_and_reject_invalid_dna():
    dna = 'A' * 30 + 'G' * 30
    result = codon_metrics(dna, window_nt=30, stride_nt=3)
    windows = result['gc_windows']
    assert len(windows) == 11
    assert [x['start_nt'] for x in windows] == list(range(0, 31, 3))
    assert windows[1]['gc_fraction'] == pytest.approx(.1)
    assert windows[-1]['gc_fraction'] == 1
    with pytest.raises(ValueError): codon_metrics('ATGNAA')


def test_sbml_core_document_semantics():
    text = sbml_export(['step a', 'step b'], {'step a': 1.5})
    ns = {'s': 'http://www.sbml.org/sbml/level3/version2/core'}
    root = ET.fromstring(text)
    assert root.tag == '{' + ns['s'] + '}sbml'
    compartment = root.find('s:model/s:listOfCompartments/s:compartment', ns)
    assert compartment.attrib['id'] == 'cell' and compartment.attrib['constant'] == 'true'
    species = root.findall('s:model/s:listOfSpecies/s:species', ns)
    assert len(species) == 3 and all(x.attrib['compartment'] == 'cell' for x in species)
    reactions = root.findall('s:model/s:listOfReactions/s:reaction', ns)
    assert len(reactions) == 2
    assert reactions[0].find('s:listOfReactants/s:speciesReference', ns).attrib['species'] == 'S0'
    assert reactions[0].find('s:listOfProducts/s:speciesReference', ns).attrib['species'] == 'S1'
    assert 'estimatedFlux' not in reactions[0].attrib


def test_sbml_parser_consistency():
    import libsbml
    doc = libsbml.readSBMLFromString(sbml_export(['step a', 'step b']))
    assert doc.getNumErrors() == 0, doc.getErrorLog().toString()
    doc.checkConsistency()
    severe = [doc.getError(i).getMessage() for i in range(doc.getNumErrors()) if doc.getError(i).getSeverity() >= libsbml.LIBSBML_SEV_ERROR]
    assert not severe

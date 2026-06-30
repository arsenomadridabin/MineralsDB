"""Semantic extraction task groups for LLM-based data extraction."""

import json
import logging

from minerals.models import ExtractedRecord
from minerals.services.import_approved import validate_and_update_record

logger = logging.getLogger(__name__)

EXTRACTION_TASKS = [
    'source_phase',
    'crystal_structure',
    'eos_parameters',
    'pv_ev_data',
    'elastic_properties',
]


def _mock_llm_response(task_name, job):
    """Return mock extracted data per task group for demonstration."""
    samples = {
        'source_phase': [
            {
                'target_model': 'Source',
                'extracted_json': {
                    'doi': '10.1038/nature00000',
                    'title': 'Extracted mantle phase study',
                    'authors': ['A. Author', 'B. Researcher'],
                    'journal': 'Nature',
                    'year': 2020,
                    'source_type': 'journal',
                },
                'evidence_text': 'Published in Nature (2020), DOI: 10.1038/nature00000',
                'page_number': 1,
                'confidence': 0.92,
            },
            {
                'target_model': 'Phase',
                'extracted_json': {
                    'name': 'New Mantle Phase',
                    'formula': 'MgSiO3',
                    'mineral_group': 'silicate perovskite',
                    'phase_type': 'silicate',
                    'aliases': ['Mg-Pv'],
                    'description': 'Extracted phase from uploaded document.',
                },
                'evidence_text': 'We report a new MgSiO3 phase stable at 120 GPa.',
                'page_number': 2,
                'confidence': 0.88,
            },
        ],
        'crystal_structure': [
            {
                'target_model': 'CrystalStructure',
                'extracted_json': {
                    'phase_name': 'Bridgmanite',
                    'doi': '10.1038/nature00000',
                    'crystal_system': 'orthorhombic',
                    'space_group': 'Pnma',
                    'lattice_a': 4.77,
                    'lattice_b': 4.93,
                    'lattice_c': 6.89,
                    'volume': 162.1,
                    'pressure': 120.0,
                    'temperature': 2500.0,
                    'method': 'XRD',
                },
                'evidence_text': 'Orthorhombic Pnma structure at 120 GPa and 2500 K.',
                'page_number': 5,
                'confidence': 0.85,
            },
        ],
        'eos_parameters': [
            {
                'target_model': 'EOSEntry',
                'extracted_json': {
                    'phase_name': 'Bridgmanite',
                    'doi': '10.1038/nature00000',
                    'eos_model': 'Birch-Murnaghan',
                    'temperature': 300.0,
                    'pressure_min': 0.0,
                    'pressure_max': 140.0,
                    'method': 'DAC',
                    'parameters': [
                        {'name': 'V0', 'value': 162.5, 'unit': 'Å³', 'uncertainty': 0.5},
                        {'name': 'K0', 'value': 260.0, 'unit': 'GPa', 'uncertainty': 5.0},
                        {'name': 'K0_prime', 'value': 4.0, 'unit': '', 'uncertainty': 0.2},
                    ],
                },
                'evidence_text': 'BM EOS: V0=162.5 Å³, K0=260 GPa, K0\'=4.0',
                'page_number': 8,
                'confidence': 0.90,
            },
        ],
        'pv_ev_data': [
            {
                'target_model': 'PVData',
                'extracted_json': {
                    'phase_name': 'Bridgmanite',
                    'doi': '10.1038/nature00000',
                    'eos_model': 'Birch-Murnaghan',
                    'points': [
                        {'pressure': 0, 'volume': 162.5, 'temperature': 300, 'pressure_unit': 'GPa', 'volume_unit': 'Å³'},
                        {'pressure': 25, 'volume': 155.0, 'temperature': 300, 'pressure_unit': 'GPa', 'volume_unit': 'Å³'},
                        {'pressure': 50, 'volume': 149.0, 'temperature': 300, 'pressure_unit': 'GPa', 'volume_unit': 'Å³'},
                    ],
                },
                'evidence_text': 'P-V data table, page 9.',
                'page_number': 9,
                'confidence': 0.87,
            },
            {
                'target_model': 'EVData',
                'extracted_json': {
                    'phase_name': 'Bridgmanite',
                    'doi': '10.1038/nature00000',
                    'points': [
                        {'energy': -8.10, 'volume': 162.5, 'energy_unit': 'eV/atom', 'volume_unit': 'Å³'},
                        {'energy': -8.05, 'volume': 155.0, 'energy_unit': 'eV/atom', 'volume_unit': 'Å³'},
                    ],
                },
                'evidence_text': 'E-V curve from DFT calculations, Fig. 3.',
                'page_number': 10,
                'confidence': 0.86,
            },
        ],
        'elastic_properties': [
            {
                'target_model': 'ElasticMeasurement',
                'extracted_json': {
                    'phase_name': 'Bridgmanite',
                    'doi': '10.1038/nature00000',
                    'pressure': 120.0,
                    'temperature': 2500.0,
                    'bulk_modulus': 280.0,
                    'shear_modulus': 150.0,
                    'vp': 12.5,
                    'vs': 6.8,
                    'pressure_unit': 'GPa',
                    'temperature_unit': 'K',
                    'method': 'Brillouin spectroscopy',
                },
                'evidence_text': 'Elastic moduli at 120 GPa and 2500 K from Brillouin measurements.',
                'page_number': 12,
                'confidence': 0.84,
            },
        ],
    }
    return samples.get(task_name, [])


def run_extraction_tasks(job):
    """Run all semantic extraction task groups and save to ExtractedRecord."""
    for task in EXTRACTION_TASKS:
        logger.info('Running extraction task: %s for job %s', task, job.pk)
        results = _mock_llm_response(task, job)
        for item in results:
            record = ExtractedRecord.objects.create(
                extraction_job=job,
                target_model=item['target_model'],
                extracted_json=item['extracted_json'],
                evidence_text=item.get('evidence_text', ''),
                page_number=item.get('page_number'),
                confidence=item.get('confidence'),
            )
            validate_and_update_record(record)


def format_extraction_prompt(task_name, document_text):
    """Build prompt for a semantic extraction task (for real LLM integration)."""
    prompts = {
        'source_phase': (
            'Extract bibliographic metadata and mineral phase definitions from this document. '
            'Return JSON with source fields (doi, title, authors, journal, year) and phase fields '
            '(name, formula, mineral_group, phase_type, aliases). '
            'Each value must include value, unit (if applicable), evidence_text, page_number, '
            f'and confidence score.\n\n{document_text[:8000]}'
        ),
        'crystal_structure': (
            'Extract crystal structure data including space group, lattice parameters, volume, '
            'density, pressure, and temperature conditions.\n\n' + document_text[:8000]
        ),
        'eos_parameters': (
            'Extract equation of state model name and parameters (V0, K0, K0_prime, etc.) '
            'with units and uncertainties.\n\n' + document_text[:8000]
        ),
        'pv_ev_data': (
            'Extract pressure-volume and energy-volume data points with units.\n\n'
            + document_text[:8000]
        ),
        'elastic_properties': (
            'Extract elastic and seismic properties: bulk modulus, shear modulus, Vp, Vs, '
            'density at given P-T conditions.\n\n' + document_text[:8000]
        ),
    }
    return prompts.get(task_name, document_text[:8000])

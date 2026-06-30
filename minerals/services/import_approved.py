"""Import approved ExtractedRecord rows into final scientific tables."""

import logging

from django.db import transaction
from django.utils import timezone

from minerals.models import (
    CrystalStructure,
    ElasticMeasurement,
    EOSParameter,
    EOSEntry,
    EVData,
    ExtractedRecord,
    Phase,
    PVData,
    Source,
)
from minerals.validators import validate_extracted_record

logger = logging.getLogger(__name__)


def _get_or_create_phase(data):
    name = data.get('name', '').strip()
    phase, created = Phase.objects.get_or_create(
        name=name,
        defaults={
            'formula': data.get('formula', ''),
            'mineral_group': data.get('mineral_group', ''),
            'phase_type': data.get('phase_type', 'silicate'),
            'aliases': data.get('aliases', []),
            'description': data.get('description', ''),
        },
    )
    return phase, created


def _get_or_create_source(data):
    doi = data.get('doi', '').strip()
    if doi:
        source, created = Source.objects.get_or_create(
            doi=doi,
            defaults={
                'title': data.get('title', 'Untitled'),
                'authors': data.get('authors', []),
                'journal': data.get('journal', ''),
                'year': data.get('year'),
                'source_type': data.get('source_type', 'journal'),
                'url': data.get('url', ''),
                'database_name': data.get('database_name', ''),
            },
        )
    else:
        source = Source.objects.create(
            title=data.get('title', 'Untitled'),
            authors=data.get('authors', []),
            journal=data.get('journal', ''),
            year=data.get('year'),
            source_type=data.get('source_type', 'journal'),
            url=data.get('url', ''),
            database_name=data.get('database_name', ''),
        )
        created = True
    return source, created


def _resolve_phase(data):
    phase_id = data.get('phase_id')
    phase_name = data.get('phase_name') or data.get('name')
    if phase_id:
        return Phase.objects.get(pk=phase_id)
    if phase_name:
        return Phase.objects.filter(name__iexact=phase_name.strip()).first()
    return None


def _resolve_source(data):
    source_id = data.get('source_id')
    doi = data.get('doi')
    if source_id:
        return Source.objects.get(pk=source_id)
    if doi:
        return Source.objects.filter(doi=doi).first()
    return None


def _resolve_eos_entry(data):
    eos_entry_id = data.get('eos_entry_id')
    if eos_entry_id:
        return EOSEntry.objects.get(pk=eos_entry_id)
    phase = _resolve_phase(data)
    source = _resolve_source(data)
    eos_model = data.get('eos_model')
    if phase and source:
        qs = EOSEntry.objects.filter(phase=phase, source=source)
        if eos_model:
            qs = qs.filter(eos_model=eos_model)
        return qs.first()
    return None


def import_record(record: ExtractedRecord):
    """Insert a single approved ExtractedRecord into the target table."""
    if record.reviewer_status != 'approved':
        raise ValueError('Only approved records can be imported.')

    data = record.extracted_json
    target = record.target_model

    with transaction.atomic():
        if target == 'Phase':
            _get_or_create_phase(data)

        elif target == 'Source':
            _get_or_create_source(data)

        elif target == 'CrystalStructure':
            phase = _resolve_phase(data)
            source = _resolve_source(data)
            if not phase or not source:
                raise ValueError('CrystalStructure requires valid phase and source references.')
            CrystalStructure.objects.create(
                phase=phase,
                source=source,
                crystal_system=data.get('crystal_system', ''),
                space_group=data.get('space_group', ''),
                lattice_a=data.get('lattice_a'),
                lattice_b=data.get('lattice_b'),
                lattice_c=data.get('lattice_c'),
                alpha=data.get('alpha'),
                beta=data.get('beta'),
                gamma=data.get('gamma'),
                volume=data.get('volume'),
                density=data.get('density'),
                coordinate_type=data.get('coordinate_type', 'fractional'),
                method=data.get('method', ''),
                pressure=data.get('pressure'),
                temperature=data.get('temperature'),
            )

        elif target == 'EOSEntry':
            phase = _resolve_phase(data)
            source = _resolve_source(data)
            if not phase or not source:
                raise ValueError('EOSEntry requires valid phase and source references.')
            eos = EOSEntry.objects.create(
                phase=phase,
                source=source,
                eos_model=data.get('eos_model', 'Birch-Murnaghan'),
                temperature=data.get('temperature'),
                pressure_min=data.get('pressure_min'),
                pressure_max=data.get('pressure_max'),
                volume_min=data.get('volume_min'),
                volume_max=data.get('volume_max'),
                method=data.get('method', ''),
                notes=data.get('notes', ''),
            )
            for param in data.get('parameters', []):
                EOSParameter.objects.create(
                    eos_entry=eos,
                    name=param.get('name', ''),
                    value=param.get('value'),
                    unit=param.get('unit', ''),
                    uncertainty=param.get('uncertainty'),
                )

        elif target == 'EOSParameter':
            eos_entry_id = data.get('eos_entry_id')
            if not eos_entry_id:
                raise ValueError('EOSParameter requires eos_entry_id.')
            EOSParameter.objects.create(
                eos_entry_id=eos_entry_id,
                name=data.get('name', ''),
                value=data.get('value'),
                unit=data.get('unit', ''),
                uncertainty=data.get('uncertainty'),
            )

        elif target == 'PVData':
            eos_entry = _resolve_eos_entry(data)
            if not eos_entry:
                raise ValueError('PVData requires eos_entry_id or phase/source references.')
            points = data.get('points', [data])
            for pt in points:
                PVData.objects.create(
                    eos_entry=eos_entry,
                    pressure=pt.get('pressure', data.get('pressure')),
                    volume=pt.get('volume', data.get('volume')),
                    temperature=pt.get('temperature', data.get('temperature')),
                    pressure_unit=pt.get('pressure_unit', data.get('pressure_unit', 'GPa')),
                    volume_unit=pt.get('volume_unit', data.get('volume_unit', 'Å³')),
                )

        elif target == 'EVData':
            eos_entry = _resolve_eos_entry(data)
            if not eos_entry:
                raise ValueError('EVData requires eos_entry_id or phase/source references.')
            points = data.get('points', [data])
            for pt in points:
                EVData.objects.create(
                    eos_entry=eos_entry,
                    energy=pt.get('energy', data.get('energy')),
                    volume=pt.get('volume', data.get('volume')),
                    energy_unit=pt.get('energy_unit', data.get('energy_unit', 'eV/atom')),
                    volume_unit=pt.get('volume_unit', data.get('volume_unit', 'Å³')),
                )

        elif target == 'ElasticMeasurement':
            phase = _resolve_phase(data)
            source = _resolve_source(data)
            if not phase or not source:
                raise ValueError('ElasticMeasurement requires valid phase and source references.')
            ElasticMeasurement.objects.create(
                phase=phase,
                source=source,
                pressure=data.get('pressure'),
                temperature=data.get('temperature'),
                density=data.get('density'),
                bulk_modulus=data.get('bulk_modulus'),
                shear_modulus=data.get('shear_modulus'),
                vp=data.get('vp'),
                vs=data.get('vs'),
                pressure_unit=data.get('pressure_unit', 'GPa'),
                temperature_unit=data.get('temperature_unit', 'K'),
                density_unit=data.get('density_unit', 'g/cm³'),
                modulus_unit=data.get('modulus_unit', 'GPa'),
                velocity_unit=data.get('velocity_unit', 'km/s'),
                method=data.get('method', ''),
            )

        else:
            raise ValueError(f'Unknown target model: {target}')


def validate_and_update_record(record: ExtractedRecord):
    """Run validation rules and update validation_status."""
    errors = validate_extracted_record(record.extracted_json, record.target_model)

    if record.target_model in (
        'CrystalStructure', 'EOSEntry', 'ElasticMeasurement', 'EOSParameter', 'PVData', 'EVData'
    ):
        phase_name = record.extracted_json.get('phase_name') or record.extracted_json.get('name')
        if phase_name and not Phase.objects.filter(name__iexact=phase_name.strip()).exists():
            errors.append(
                f'Phase "{phase_name}" not found in database — flagged for review.'
            )

    record.validation_status = 'invalid' if errors else 'valid'
    if errors:
        record.reviewer_notes = '; '.join(errors)
    record.save(update_fields=['validation_status', 'reviewer_notes'])
    return errors


def run_mock_extraction(job):
    """
    Simulate LLM extraction with semantic task groups.
    In production, replace with actual LLM API calls.
    """
    from minerals.services.extraction import EXTRACTION_TASKS, run_extraction_tasks

    run_extraction_tasks(job)
    job.status = 'completed'
    job.completed_at = timezone.now()
    job.save(update_fields=['status', 'completed_at'])

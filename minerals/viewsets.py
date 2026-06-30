import json

from django.db.models import Count, Q
from rest_framework import viewsets

from .models import (
    CrystalStructure,
    ElasticMeasurement,
    EOSParameter,
    EOSEntry,
    EVData,
    ExtractedRecord,
    ExtractionJob,
    Phase,
    PVData,
    Source,
)
from .serializers import (
    CrystalStructureSerializer,
    ElasticMeasurementSerializer,
    EOSParameterSerializer,
    EOSEntrySerializer,
    EVDataSerializer,
    ExtractedRecordSerializer,
    ExtractionJobSerializer,
    PhaseSerializer,
    PVDataSerializer,
    SourceSerializer,
)


class PhaseViewSet(viewsets.ModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    search_fields = ['name', 'formula', 'mineral_group', 'phase_type', 'aliases']
    ordering_fields = ['name', 'formula', 'mineral_group']


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    search_fields = ['doi', 'title', 'journal', 'authors']
    ordering_fields = ['year', 'title', 'journal']


class CrystalStructureViewSet(viewsets.ModelViewSet):
    queryset = CrystalStructure.objects.select_related('phase', 'source')
    serializer_class = CrystalStructureSerializer
    search_fields = ['phase__name', 'space_group', 'crystal_system', 'method']
    ordering_fields = ['pressure', 'temperature']


class EOSEntryViewSet(viewsets.ModelViewSet):
    queryset = EOSEntry.objects.select_related('phase', 'source').prefetch_related(
        'parameters', 'pv_data', 'ev_data'
    )
    serializer_class = EOSEntrySerializer
    search_fields = ['phase__name', 'eos_model', 'method']
    ordering_fields = ['temperature', 'eos_model']


class EOSParameterViewSet(viewsets.ModelViewSet):
    queryset = EOSParameter.objects.select_related('eos_entry')
    serializer_class = EOSParameterSerializer
    search_fields = ['name', 'eos_entry__phase__name']


class PVDataViewSet(viewsets.ModelViewSet):
    queryset = PVData.objects.select_related('eos_entry')
    serializer_class = PVDataSerializer
    ordering_fields = ['pressure', 'temperature']


class EVDataViewSet(viewsets.ModelViewSet):
    queryset = EVData.objects.select_related('eos_entry')
    serializer_class = EVDataSerializer
    ordering_fields = ['volume', 'energy']


class ElasticMeasurementViewSet(viewsets.ModelViewSet):
    queryset = ElasticMeasurement.objects.select_related('phase', 'source')
    serializer_class = ElasticMeasurementSerializer
    search_fields = ['phase__name', 'method']
    ordering_fields = ['pressure', 'temperature']


class ExtractionJobViewSet(viewsets.ModelViewSet):
    queryset = ExtractionJob.objects.prefetch_related('extracted_records')
    serializer_class = ExtractionJobSerializer
    ordering_fields = ['created_at', 'status']


class ExtractedRecordViewSet(viewsets.ModelViewSet):
    queryset = ExtractedRecord.objects.select_related('extraction_job')
    serializer_class = ExtractedRecordSerializer
    search_fields = ['target_model', 'evidence_text']
    ordering_fields = ['created_at', 'confidence']


def build_phase_queryset(request):
    qs = Phase.objects.annotate(
        eos_entry_count=Count('eos_entries', distinct=True),
        crystal_structure_count=Count('crystal_structures', distinct=True),
        elastic_measurement_count=Count('elastic_measurements', distinct=True),
    )
    q = request.GET.get('q', '').strip()
    formula = request.GET.get('formula', '').strip()
    mineral_group = request.GET.get('mineral_group', '').strip()
    phase_type = request.GET.get('phase_type', '').strip()

    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(formula__icontains=q)
            | Q(aliases__icontains=q)
            | Q(description__icontains=q)
        )
    if formula:
        qs = qs.filter(formula__icontains=formula)
    if mineral_group:
        qs = qs.filter(mineral_group__icontains=mineral_group)
    if phase_type:
        qs = qs.filter(phase_type__icontains=phase_type)
    return qs.order_by('name')


def get_phase_source_count(phase):
    source_ids = set()
    for cs in phase.crystal_structures.all():
        source_ids.add(cs.source_id)
    for eos in phase.eos_entries.all():
        source_ids.add(eos.source_id)
    for em in phase.elastic_measurements.all():
        source_ids.add(em.source_id)
    return len(source_ids)


def global_search(query):
    if not query:
        return {}

    q = query.strip()
    results = {
        'phases': Phase.objects.filter(
            Q(name__icontains=q) | Q(formula__icontains=q) | Q(aliases__icontains=q)
        )[:20],
        'sources': Source.objects.filter(
            Q(doi__icontains=q) | Q(title__icontains=q) | Q(journal__icontains=q)
        )[:20],
        'eos_entries': EOSEntry.objects.filter(
            Q(eos_model__icontains=q) | Q(method__icontains=q) | Q(phase__name__icontains=q)
        ).select_related('phase', 'source')[:20],
        'crystal_structures': CrystalStructure.objects.filter(
            Q(space_group__icontains=q)
            | Q(crystal_system__icontains=q)
            | Q(phase__name__icontains=q)
            | Q(method__icontains=q)
        ).select_related('phase', 'source')[:20],
        'elastic_measurements': ElasticMeasurement.objects.filter(
            Q(method__icontains=q) | Q(phase__name__icontains=q)
        ).select_related('phase', 'source')[:20],
    }
    return results


def build_plot_data(phase):
    """Prepare PV and EV plot data grouped by EOS entry."""
    pv_series = []
    ev_series = []

    for eos in phase.eos_entries.prefetch_related('pv_data', 'ev_data', 'source').all():
        label = f'{eos.eos_model}'
        if eos.temperature:
            label += f' @ {eos.temperature} K'
        source_label = eos.source.title[:40] if eos.source else ''
        full_label = f'{label} ({source_label})'

        pv_points = list(
            eos.pv_data.order_by('pressure').values('pressure', 'volume', 'pressure_unit', 'volume_unit')
        )
        if pv_points:
            pv_series.append({
                'label': full_label,
                'eos_id': eos.pk,
                'pressure_unit': pv_points[0]['pressure_unit'],
                'volume_unit': pv_points[0]['volume_unit'],
                'points': pv_points,
            })

        ev_points = list(
            eos.ev_data.order_by('volume').values('energy', 'volume', 'energy_unit', 'volume_unit')
        )
        if ev_points:
            ev_series.append({
                'label': full_label,
                'eos_id': eos.pk,
                'energy_unit': ev_points[0]['energy_unit'],
                'volume_unit': ev_points[0]['volume_unit'],
                'points': ev_points,
            })

    return {
        'pv_series': pv_series,
        'ev_series': ev_series,
        'pv_json': json.dumps(pv_series),
        'ev_json': json.dumps(ev_series),
    }

import json

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from .forms import ExtractionUploadForm, HomeFilterForm, PhaseFilterForm, RecordReviewForm
from .models import (
    CrystalStructure,
    ElasticMeasurement,
    EOSEntry,
    EVData,
    ExtractedRecord,
    ExtractionJob,
    Phase,
    PVData,
    Source,
)
from .services.import_approved import import_record, run_mock_extraction, validate_and_update_record
from .viewsets import build_phase_queryset, build_plot_data, get_phase_source_count, global_search


class HomeView(View):
    template_name = 'minerals/home.html'

    def get(self, request):
        form = HomeFilterForm(request.GET or None)
        phases = Phase.objects.all()[:12]

        if form.is_valid() and any(form.cleaned_data.values()):
            phases = self._filter_phases(form.cleaned_data)

        context = {
            'form': form,
            'phases': phases,
            'total_phases': Phase.objects.count(),
            'total_sources': Source.objects.count(),
            'total_eos': EOSEntry.objects.count(),
        }
        return render(request, self.template_name, context)

    def _filter_phases(self, data):
        qs = Phase.objects.all()
        if data.get('q'):
            qs = qs.filter(
                Q(name__icontains=data['q'])
                | Q(formula__icontains=data['q'])
                | Q(aliases__icontains=data['q'])
            )
        if data.get('formula'):
            qs = qs.filter(formula__icontains=data['formula'])
        if data.get('mineral_group'):
            qs = qs.filter(mineral_group__icontains=data['mineral_group'])
        if data.get('phase_type'):
            qs = qs.filter(phase_type__icontains=data['phase_type'])
        if data.get('eos_model'):
            qs = qs.filter(eos_entries__eos_model__icontains=data['eos_model']).distinct()
        if data.get('source_year'):
            qs = qs.filter(
                Q(eos_entries__source__year=data['source_year'])
                | Q(crystal_structures__source__year=data['source_year'])
                | Q(elastic_measurements__source__year=data['source_year'])
            ).distinct()
        if data.get('method'):
            qs = qs.filter(
                Q(eos_entries__method__icontains=data['method'])
                | Q(crystal_structures__method__icontains=data['method'])
                | Q(elastic_measurements__method__icontains=data['method'])
            ).distinct()
        if data.get('pressure_min') is not None:
            qs = qs.filter(
                Q(eos_entries__pv_data__pressure__gte=data['pressure_min'])
                | Q(elastic_measurements__pressure__gte=data['pressure_min'])
            ).distinct()
        if data.get('pressure_max') is not None:
            qs = qs.filter(
                Q(eos_entries__pv_data__pressure__lte=data['pressure_max'])
                | Q(elastic_measurements__pressure__lte=data['pressure_max'])
            ).distinct()
        if data.get('temperature_min') is not None:
            qs = qs.filter(
                Q(eos_entries__temperature__gte=data['temperature_min'])
                | Q(elastic_measurements__temperature__gte=data['temperature_min'])
            ).distinct()
        if data.get('temperature_max') is not None:
            qs = qs.filter(
                Q(eos_entries__temperature__lte=data['temperature_max'])
                | Q(elastic_measurements__temperature__lte=data['temperature_max'])
            ).distinct()
        return qs.distinct()[:24]


class PhaseListView(ListView):
    model = Phase
    template_name = 'minerals/phase_list.html'
    context_object_name = 'phases'
    paginate_by = 25

    def get_queryset(self):
        qs = build_phase_queryset(self.request)
        return qs.prefetch_related(
            'crystal_structures', 'eos_entries', 'elastic_measurements'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = PhaseFilterForm(self.request.GET)
        for phase in context['phases']:
            phase.source_count = get_phase_source_count(phase)
        return context


class PhaseDetailView(DetailView):
    model = Phase
    template_name = 'minerals/phase_detail.html'
    context_object_name = 'phase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phase = self.object

        source_ids = set()
        for rel in (phase.crystal_structures, phase.eos_entries, phase.elastic_measurements):
            for obj in rel.select_related('source').all():
                source_ids.add(obj.source_id)
        context['sources'] = Source.objects.filter(pk__in=source_ids).order_by('-year')

        context['crystal_structures'] = phase.crystal_structures.select_related('source').all()
        context['eos_entries'] = phase.eos_entries.select_related('source').prefetch_related(
            'parameters', 'pv_data', 'ev_data'
        )
        context['elastic_measurements'] = phase.elastic_measurements.select_related('source').all()

        eos_params = {}
        for eos in context['eos_entries']:
            eos_params[eos.pk] = eos.parameters.all()
        context['eos_params_by_entry'] = eos_params

        all_pv = PVData.objects.filter(eos_entry__phase=phase).select_related(
            'eos_entry', 'eos_entry__source'
        )
        all_ev = EVData.objects.filter(eos_entry__phase=phase).select_related(
            'eos_entry', 'eos_entry__source'
        )
        context['pv_data'] = all_pv
        context['ev_data'] = all_ev
        context.update(build_plot_data(phase))
        return context


class SourceDetailView(DetailView):
    model = Source
    template_name = 'minerals/source_detail.html'
    context_object_name = 'source'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        source = self.object

        phase_ids = set()
        for cs in source.crystal_structures.all():
            phase_ids.add(cs.phase_id)
        for eos in source.eos_entries.all():
            phase_ids.add(eos.phase_id)
        for em in source.elastic_measurements.all():
            phase_ids.add(em.phase_id)

        context['phases'] = Phase.objects.filter(pk__in=phase_ids)
        context['crystal_structures'] = source.crystal_structures.select_related('phase').all()
        context['eos_entries'] = source.eos_entries.select_related('phase').prefetch_related(
            'parameters', 'pv_data', 'ev_data'
        )
        context['pv_data'] = PVData.objects.filter(eos_entry__source=source).select_related(
            'eos_entry', 'eos_entry__phase'
        )
        context['ev_data'] = EVData.objects.filter(eos_entry__source=source).select_related(
            'eos_entry', 'eos_entry__phase'
        )
        context['elastic_measurements'] = source.elastic_measurements.select_related('phase').all()
        return context


class SearchView(View):
    template_name = 'minerals/search_results.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        results = global_search(query) if query else {}
        return render(request, self.template_name, {'query': query, 'results': results})


class ExtractionUploadView(View):
    template_name = 'minerals/extraction/upload.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ExtractionUploadForm()})

    def post(self, request):
        form = ExtractionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.status = 'processing'
            job.save()
            run_mock_extraction(job)
            messages.success(request, f'Extraction job #{job.pk} completed. Review extracted records.')
            return redirect('extraction_job_detail', pk=job.pk)
        return render(request, self.template_name, {'form': form})


class ExtractionJobListView(ListView):
    model = ExtractionJob
    template_name = 'minerals/extraction/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 20


class ExtractionJobDetailView(DetailView):
    model = ExtractionJob
    template_name = 'minerals/extraction/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['records'] = self.object.extracted_records.all()
        return context


class RecordReviewView(View):
    template_name = 'minerals/extraction/record_review.html'

    def get(self, request, pk):
        record = get_object_or_404(ExtractedRecord, pk=pk)
        return render(request, self.template_name, {
            'record': record,
            'record_json': json.dumps(record.extracted_json, indent=2),
            'form': RecordReviewForm(),
        })

    def post(self, request, pk):
        record = get_object_or_404(ExtractedRecord, pk=pk)
        form = RecordReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['reviewer_notes']
            record.reviewer_notes = notes

            if action == 'approve':
                validate_and_update_record(record)
                if record.validation_status == 'invalid':
                    messages.error(request, f'Validation failed: {record.reviewer_notes}')
                else:
                    record.reviewer_status = 'approved'
                    record.save()
                    try:
                        import_record(record)
                        messages.success(request, 'Record approved and imported into database.')
                    except Exception as exc:
                        messages.error(request, f'Import failed: {exc}')
            else:
                record.reviewer_status = 'rejected'
                record.save()
                messages.info(request, 'Record rejected.')

            return redirect('extraction_job_detail', pk=record.extraction_job_id)

        return render(request, self.template_name, {'record': record, 'form': form})

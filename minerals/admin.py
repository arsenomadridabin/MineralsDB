from django.contrib import admin

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


class EOSParameterInline(admin.TabularInline):
    model = EOSParameter
    extra = 1


class PVDataInline(admin.TabularInline):
    model = PVData
    extra = 0


class EVDataInline(admin.TabularInline):
    model = EVData
    extra = 0


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'formula', 'mineral_group', 'phase_type')
    list_filter = ('mineral_group', 'phase_type')
    search_fields = ('name', 'formula', 'mineral_group', 'phase_type')


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'doi', 'journal', 'year', 'source_type')
    list_filter = ('year', 'source_type', 'journal')
    search_fields = ('doi', 'title', 'journal', 'year')


@admin.register(CrystalStructure)
class CrystalStructureAdmin(admin.ModelAdmin):
    list_display = ('phase', 'space_group', 'crystal_system', 'pressure', 'temperature', 'method')
    list_filter = ('crystal_system', 'space_group', 'method')
    search_fields = ('phase__name', 'space_group', 'crystal_system')
    raw_id_fields = ('phase', 'source')


@admin.register(EOSEntry)
class EOSEntryAdmin(admin.ModelAdmin):
    list_display = ('phase', 'eos_model', 'temperature', 'method', 'source')
    list_filter = ('eos_model', 'method', 'temperature')
    search_fields = ('phase__name', 'eos_model', 'method')
    raw_id_fields = ('phase', 'source')
    inlines = [EOSParameterInline, PVDataInline, EVDataInline]


@admin.register(EOSParameter)
class EOSParameterAdmin(admin.ModelAdmin):
    list_display = ('eos_entry', 'name', 'value', 'unit', 'uncertainty')
    list_filter = ('name',)
    search_fields = ('name', 'eos_entry__phase__name')
    raw_id_fields = ('eos_entry',)


@admin.register(PVData)
class PVDataAdmin(admin.ModelAdmin):
    list_display = ('eos_entry', 'pressure', 'volume', 'temperature', 'pressure_unit')
    list_filter = ('pressure_unit', 'volume_unit')
    raw_id_fields = ('eos_entry',)


@admin.register(EVData)
class EVDataAdmin(admin.ModelAdmin):
    list_display = ('eos_entry', 'energy', 'volume', 'energy_unit')
    list_filter = ('energy_unit', 'volume_unit')
    raw_id_fields = ('eos_entry',)


@admin.register(ElasticMeasurement)
class ElasticMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        'phase', 'pressure', 'temperature', 'bulk_modulus', 'shear_modulus', 'vp', 'vs', 'method'
    )
    list_filter = ('method', 'pressure_unit')
    search_fields = ('phase__name', 'method')
    raw_id_fields = ('phase', 'source')


class ExtractedRecordInline(admin.TabularInline):
    model = ExtractedRecord
    extra = 0
    readonly_fields = ('created_at',)
    fields = (
        'target_model',
        'validation_status',
        'reviewer_status',
        'confidence',
        'page_number',
        'created_at',
    )


@admin.register(ExtractionJob)
class ExtractionJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'model_name', 'prompt_version', 'created_at', 'completed_at')
    list_filter = ('status', 'model_name')
    readonly_fields = ('created_at',)
    inlines = [ExtractedRecordInline]


@admin.register(ExtractedRecord)
class ExtractedRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'extraction_job',
        'target_model',
        'validation_status',
        'reviewer_status',
        'confidence',
        'page_number',
        'created_at',
    )
    list_filter = ('target_model', 'validation_status', 'reviewer_status')
    search_fields = ('evidence_text', 'extracted_json')
    readonly_fields = ('created_at',)

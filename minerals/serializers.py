from rest_framework import serializers

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


class PhaseSerializer(serializers.ModelSerializer):
    source_count = serializers.SerializerMethodField()
    eos_entry_count = serializers.SerializerMethodField()
    crystal_structure_count = serializers.SerializerMethodField()
    elastic_measurement_count = serializers.SerializerMethodField()

    class Meta:
        model = Phase
        fields = '__all__'

    def _distinct_source_count(self, obj):
        source_ids = set()
        for cs in obj.crystal_structures.all():
            source_ids.add(cs.source_id)
        for eos in obj.eos_entries.all():
            source_ids.add(eos.source_id)
        for em in obj.elastic_measurements.all():
            source_ids.add(em.source_id)
        return len(source_ids)

    def get_source_count(self, obj):
        return self._distinct_source_count(obj)

    def get_eos_entry_count(self, obj):
        return obj.eos_entries.count()

    def get_crystal_structure_count(self, obj):
        return obj.crystal_structures.count()

    def get_elastic_measurement_count(self, obj):
        return obj.elastic_measurements.count()


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = '__all__'


class CrystalStructureSerializer(serializers.ModelSerializer):
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    source_title = serializers.CharField(source='source.title', read_only=True)

    class Meta:
        model = CrystalStructure
        fields = '__all__'


class EOSParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = EOSParameter
        fields = '__all__'


class PVDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PVData
        fields = '__all__'


class EVDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = EVData
        fields = '__all__'


class EOSEntrySerializer(serializers.ModelSerializer):
    parameters = EOSParameterSerializer(many=True, read_only=True)
    pv_data = PVDataSerializer(many=True, read_only=True)
    ev_data = EVDataSerializer(many=True, read_only=True)
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    source_title = serializers.CharField(source='source.title', read_only=True)

    class Meta:
        model = EOSEntry
        fields = '__all__'


class ElasticMeasurementSerializer(serializers.ModelSerializer):
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    source_title = serializers.CharField(source='source.title', read_only=True)

    class Meta:
        model = ElasticMeasurement
        fields = '__all__'


class ExtractedRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedRecord
        fields = '__all__'


class ExtractionJobSerializer(serializers.ModelSerializer):
    extracted_records = ExtractedRecordSerializer(many=True, read_only=True)

    class Meta:
        model = ExtractionJob
        fields = '__all__'

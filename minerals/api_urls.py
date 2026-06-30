from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import (
    CrystalStructureViewSet,
    ElasticMeasurementViewSet,
    EOSParameterViewSet,
    EOSEntryViewSet,
    EVDataViewSet,
    ExtractedRecordViewSet,
    ExtractionJobViewSet,
    PhaseViewSet,
    PVDataViewSet,
    SourceViewSet,
)

router = DefaultRouter()
router.register(r'phases', PhaseViewSet)
router.register(r'sources', SourceViewSet)
router.register(r'crystal-structures', CrystalStructureViewSet)
router.register(r'eos-entries', EOSEntryViewSet)
router.register(r'eos-parameters', EOSParameterViewSet)
router.register(r'pv-data', PVDataViewSet)
router.register(r'ev-data', EVDataViewSet)
router.register(r'elastic-measurements', ElasticMeasurementViewSet)
router.register(r'extraction-jobs', ExtractionJobViewSet)
router.register(r'extracted-records', ExtractedRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

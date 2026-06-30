from django.urls import path

from .views import (
    ExtractionJobDetailView,
    ExtractionJobListView,
    ExtractionUploadView,
    HomeView,
    PhaseDetailView,
    PhaseListView,
    RecordReviewView,
    SearchView,
    SourceDetailView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('phases/', PhaseListView.as_view(), name='phase_list'),
    path('phases/<int:pk>/', PhaseDetailView.as_view(), name='phase_detail'),
    path('sources/<int:pk>/', SourceDetailView.as_view(), name='source_detail'),
    path('search/', SearchView.as_view(), name='search'),
    path('extraction/upload/', ExtractionUploadView.as_view(), name='extraction_upload'),
    path('extraction/jobs/', ExtractionJobListView.as_view(), name='extraction_job_list'),
    path('extraction/jobs/<int:pk>/', ExtractionJobDetailView.as_view(), name='extraction_job_detail'),
    path('extraction/records/<int:pk>/review/', RecordReviewView.as_view(), name='record_review'),
]

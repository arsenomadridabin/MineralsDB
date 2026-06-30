from django import forms

from .models import ExtractionJob


class PhaseFilterForm(forms.Form):
    q = forms.CharField(required=False, label='Keyword')
    formula = forms.CharField(required=False)
    mineral_group = forms.CharField(required=False)
    phase_type = forms.CharField(required=False)


class GlobalSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Search')


class HomeFilterForm(forms.Form):
    q = forms.CharField(required=False, label='Search')
    formula = forms.CharField(required=False)
    mineral_group = forms.CharField(required=False)
    phase_type = forms.CharField(required=False)
    eos_model = forms.CharField(required=False)
    source_year = forms.IntegerField(required=False, min_value=1800, max_value=2100)
    method = forms.CharField(required=False)
    pressure_min = forms.FloatField(required=False, label='Min pressure (GPa)')
    pressure_max = forms.FloatField(required=False, label='Max pressure (GPa)')
    temperature_min = forms.FloatField(required=False, label='Min temperature (K)')
    temperature_max = forms.FloatField(required=False, label='Max temperature (K)')


class ExtractionUploadForm(forms.ModelForm):
    class Meta:
        model = ExtractionJob
        fields = ['uploaded_file', 'model_name', 'prompt_version', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class RecordReviewForm(forms.Form):
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    reviewer_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

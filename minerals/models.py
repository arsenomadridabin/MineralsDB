from django.db import models

from .validators import (
    ALLOWED_EOS_MODELS,
    validate_doi,
    validate_positive,
    validate_pressure_unit,
    validate_temperature_unit,
)


class Phase(models.Model):
    PHASE_TYPE_CHOICES = [
        ('silicate', 'Silicate'),
        ('oxide', 'Oxide'),
        ('carbonate', 'Carbonate'),
        ('metal', 'Metal'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200, db_index=True)
    formula = models.CharField(max_length=100, db_index=True)
    mineral_group = models.CharField(max_length=100, blank=True)
    phase_type = models.CharField(max_length=50, choices=PHASE_TYPE_CHOICES, default='silicate')
    aliases = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['formula']),
        ]

    def __str__(self):
        return self.name


class Source(models.Model):
    SOURCE_TYPE_CHOICES = [
        ('journal', 'Journal Article'),
        ('database', 'Database'),
        ('book', 'Book Chapter'),
        ('thesis', 'Thesis'),
        ('other', 'Other'),
    ]

    doi = models.CharField(max_length=255, blank=True, validators=[validate_doi], db_index=True)
    title = models.CharField(max_length=500)
    authors = models.JSONField(default=list, blank=True)
    journal = models.CharField(max_length=255, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES, default='journal')
    url = models.URLField(blank=True)
    database_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-year', 'title']
        indexes = [
            models.Index(fields=['doi']),
            models.Index(fields=['year']),
        ]

    def __str__(self):
        return f'{self.title} ({self.year or "n.d."})'


class CrystalStructure(models.Model):
    COORDINATE_TYPE_CHOICES = [
        ('fractional', 'Fractional'),
        ('cartesian', 'Cartesian'),
    ]

    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='crystal_structures')
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='crystal_structures')
    crystal_system = models.CharField(max_length=50, blank=True)
    space_group = models.CharField(max_length=50, blank=True)
    lattice_a = models.FloatField(null=True, blank=True)
    lattice_b = models.FloatField(null=True, blank=True)
    lattice_c = models.FloatField(null=True, blank=True)
    alpha = models.FloatField(null=True, blank=True)
    beta = models.FloatField(null=True, blank=True)
    gamma = models.FloatField(null=True, blank=True)
    volume = models.FloatField(null=True, blank=True)
    density = models.FloatField(null=True, blank=True)
    coordinate_type = models.CharField(
        max_length=20, choices=COORDINATE_TYPE_CHOICES, default='fractional', blank=True
    )
    cif_file = models.FileField(upload_to='cif_files/', blank=True, null=True)
    method = models.CharField(max_length=100, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['phase__name', '-pressure']
        verbose_name_plural = 'crystal structures'

    def __str__(self):
        return f'{self.phase.name} — {self.space_group or "unknown SG"}'


class EOSEntry(models.Model):
    EOS_MODEL_CHOICES = [(m, m) for m in sorted(ALLOWED_EOS_MODELS)]

    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='eos_entries')
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='eos_entries')
    eos_model = models.CharField(max_length=50, choices=EOS_MODEL_CHOICES, db_index=True)
    temperature = models.FloatField(null=True, blank=True, db_index=True)
    pressure_min = models.FloatField(null=True, blank=True)
    pressure_max = models.FloatField(null=True, blank=True)
    volume_min = models.FloatField(null=True, blank=True)
    volume_max = models.FloatField(null=True, blank=True)
    method = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['phase__name', 'eos_model']
        verbose_name = 'EOS entry'
        verbose_name_plural = 'EOS entries'
        indexes = [
            models.Index(fields=['eos_model']),
            models.Index(fields=['temperature']),
        ]

    def __str__(self):
        temp = f' @ {self.temperature} K' if self.temperature else ''
        return f'{self.phase.name} — {self.eos_model}{temp}'


class EOSParameter(models.Model):
    eos_entry = models.ForeignKey(EOSEntry, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=50)
    value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    uncertainty = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['eos_entry', 'name']
        verbose_name = 'EOS parameter'
        verbose_name_plural = 'EOS parameters'

    def __str__(self):
        return f'{self.name} = {self.value} {self.unit}'.strip()


class PVData(models.Model):
    eos_entry = models.ForeignKey(EOSEntry, on_delete=models.CASCADE, related_name='pv_data')
    pressure = models.FloatField(db_index=True)
    volume = models.FloatField()
    temperature = models.FloatField(null=True, blank=True, db_index=True)
    pressure_unit = models.CharField(max_length=10, default='GPa', validators=[validate_pressure_unit])
    volume_unit = models.CharField(max_length=10, default='Å³')

    class Meta:
        ordering = ['eos_entry', 'pressure']
        verbose_name = 'PV data point'
        verbose_name_plural = 'PV data'
        indexes = [
            models.Index(fields=['pressure']),
            models.Index(fields=['temperature']),
        ]

    def __str__(self):
        return f'P={self.pressure} {self.pressure_unit}, V={self.volume} {self.volume_unit}'


class EVData(models.Model):
    eos_entry = models.ForeignKey(EOSEntry, on_delete=models.CASCADE, related_name='ev_data')
    energy = models.FloatField()
    volume = models.FloatField(db_index=True)
    energy_unit = models.CharField(max_length=20, default='eV/atom')
    volume_unit = models.CharField(max_length=10, default='Å³')

    class Meta:
        ordering = ['eos_entry', 'volume']
        verbose_name = 'EV data point'
        verbose_name_plural = 'EV data'
        indexes = [
            models.Index(fields=['volume']),
        ]

    def __str__(self):
        return f'E={self.energy} {self.energy_unit}, V={self.volume} {self.volume_unit}'


class ElasticMeasurement(models.Model):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='elastic_measurements')
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='elastic_measurements')
    pressure = models.FloatField(null=True, blank=True, db_index=True)
    temperature = models.FloatField(null=True, blank=True, db_index=True)
    density = models.FloatField(null=True, blank=True)
    bulk_modulus = models.FloatField(null=True, blank=True)
    shear_modulus = models.FloatField(null=True, blank=True)
    vp = models.FloatField(null=True, blank=True, verbose_name='Vp')
    vs = models.FloatField(null=True, blank=True, verbose_name='Vs')
    pressure_unit = models.CharField(max_length=10, default='GPa', validators=[validate_pressure_unit])
    temperature_unit = models.CharField(
        max_length=10, default='K', validators=[validate_temperature_unit]
    )
    density_unit = models.CharField(max_length=20, default='g/cm³')
    modulus_unit = models.CharField(max_length=20, default='GPa')
    velocity_unit = models.CharField(max_length=20, default='km/s')
    method = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['phase__name', 'pressure']
        indexes = [
            models.Index(fields=['pressure']),
            models.Index(fields=['temperature']),
        ]

    def __str__(self):
        return f'{self.phase.name} elastic @ {self.pressure} {self.pressure_unit}'


class ExtractionJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    source = models.ForeignKey(
        Source, on_delete=models.SET_NULL, null=True, blank=True, related_name='extraction_jobs'
    )
    uploaded_file = models.FileField(upload_to='extraction_uploads/')
    model_name = models.CharField(max_length=100, default='gpt-4')
    prompt_version = models.CharField(max_length=50, default='v1')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'ExtractionJob #{self.pk} ({self.status})'


class ExtractedRecord(models.Model):
    TARGET_MODEL_CHOICES = [
        ('Phase', 'Phase'),
        ('Source', 'Source'),
        ('CrystalStructure', 'Crystal Structure'),
        ('EOSEntry', 'EOS Entry'),
        ('EOSParameter', 'EOS Parameter'),
        ('PVData', 'PV Data'),
        ('EVData', 'EV Data'),
        ('ElasticMeasurement', 'Elastic Measurement'),
    ]
    VALIDATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
    ]
    REVIEWER_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    extraction_job = models.ForeignKey(
        ExtractionJob, on_delete=models.CASCADE, related_name='extracted_records'
    )
    target_model = models.CharField(max_length=50, choices=TARGET_MODEL_CHOICES)
    extracted_json = models.JSONField(default=dict)
    evidence_text = models.TextField(blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    validation_status = models.CharField(
        max_length=20, choices=VALIDATION_STATUS_CHOICES, default='pending'
    )
    reviewer_status = models.CharField(
        max_length=20, choices=REVIEWER_STATUS_CHOICES, default='pending'
    )
    reviewer_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.target_model} record from job #{self.extraction_job_id}'

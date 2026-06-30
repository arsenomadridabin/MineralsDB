import re

from django.core.exceptions import ValidationError

DOI_PATTERN = re.compile(
    r'^(?:https?://(?:dx\.)?doi\.org/)?10\.\d{4,9}/[-._;()/:A-Z0-9]+',
    re.IGNORECASE,
)

ALLOWED_PRESSURE_UNITS = {'GPa', 'Pa', 'bar', 'kbar'}
ALLOWED_TEMPERATURE_UNITS = {'K', 'Celsius', '°C', 'C'}
ALLOWED_EOS_MODELS = {
    'Birch-Murnaghan',
    'Vinet',
    'Murnaghan',
    'BM3',
    'BM4',
    'Holzapfel',
    'Keane',
    'other',
}


def validate_doi(value):
    if not value:
        return
    if not DOI_PATTERN.match(value.strip()):
        raise ValidationError(
            f'"{value}" is not a valid DOI format. Expected pattern like 10.1234/example.'
        )


def validate_pressure_unit(value):
    if value and value not in ALLOWED_PRESSURE_UNITS:
        raise ValidationError(
            f'Pressure unit must be one of: {", ".join(sorted(ALLOWED_PRESSURE_UNITS))}.'
        )


def validate_temperature_unit(value):
    if value and value not in ALLOWED_TEMPERATURE_UNITS:
        raise ValidationError(
            f'Temperature unit must be one of: {", ".join(sorted(ALLOWED_TEMPERATURE_UNITS))}.'
        )


def validate_positive(value, field_name='Value'):
    if value is not None and value <= 0:
        raise ValidationError(f'{field_name} must be positive.')


def validate_eos_model(value):
    if value and value not in ALLOWED_EOS_MODELS:
        raise ValidationError(
            f'EOS model must be one of: {", ".join(sorted(ALLOWED_EOS_MODELS))}.'
        )


def validate_extracted_record(data, target_model):
    """Validate extracted JSON before approval."""
    errors = []

    if target_model == 'Source':
        doi = data.get('doi')
        if doi:
            try:
                validate_doi(doi)
            except ValidationError as exc:
                errors.append(str(exc))

    if target_model in ('EOSEntry', 'CrystalStructure', 'ElasticMeasurement'):
        pressure = data.get('pressure')
        pressure_unit = data.get('pressure_unit', 'GPa')
        if pressure is not None:
            try:
                validate_positive(float(pressure), 'Pressure')
                validate_pressure_unit(pressure_unit)
            except (ValidationError, TypeError, ValueError) as exc:
                errors.append(str(exc))

        temperature = data.get('temperature')
        temp_unit = data.get('temperature_unit', 'K')
        if temperature is not None:
            try:
                validate_temperature_unit(temp_unit)
            except ValidationError as exc:
                errors.append(str(exc))

    if target_model in ('EOSEntry', 'CrystalStructure'):
        volume = data.get('volume') or data.get('volume_min')
        if volume is not None:
            try:
                validate_positive(float(volume), 'Volume')
            except (ValidationError, TypeError, ValueError) as exc:
                errors.append(str(exc))

        eos_model = data.get('eos_model')
        if eos_model:
            try:
                validate_eos_model(eos_model)
            except ValidationError as exc:
                errors.append(str(exc))

    if target_model == 'ElasticMeasurement':
        for field in ('bulk_modulus', 'shear_modulus'):
            val = data.get(field)
            if val is not None:
                try:
                    validate_positive(float(val), field)
                except (ValidationError, TypeError, ValueError) as exc:
                    errors.append(str(exc))

    if target_model == 'Phase':
        name = data.get('name')
        if not name:
            errors.append('Phase name is required.')

    return errors

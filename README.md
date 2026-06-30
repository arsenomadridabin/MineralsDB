# Lower Mantle Mineral Database

A Django web application for browsing, searching, and visualizing lower mantle mineral data including equation-of-state (EOS) parameters, crystal structures, pressure–volume (PV) and energy–volume (EV) data, and elastic/seismic properties from the literature.

## Features

- **Searchable mineral database** — phases, formulas, aliases, literature sources, EOS models, and methods
- **Detail pages** — per-phase and per-source views with related scientific tables
- **Interactive plots** — PV and EV curves via Plotly.js, with multiple EOS entries overlaid
- **REST API** — Django REST Framework ViewSets with router-based endpoints
- **Django Admin** — full CRUD for all models
- **LLM extraction workflow** — upload papers, stage extracted JSON in `ExtractedRecord`, review/approve before import

## Tech Stack

- Django 4.2+
- Django REST Framework
- PostgreSQL (SQLite fallback for local dev)
- Bootstrap 5
- Plotly.js

## Quick Start

### 1. Clone and install dependencies

```bash
cd django_minerals
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials, or set `USE_SQLITE=true` for a quick local SQLite database.

### 3. PostgreSQL setup (recommended)

```bash
# macOS with Homebrew
brew services start postgresql
createdb mantle_minerals
```

Or with Docker:

```bash
docker run --name mantle-pg -e POSTGRES_DB=mantle_minerals \
  -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
```

### 4. Migrate and seed

```bash
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser   # optional, for admin access
```

### 5. Run the server

```bash
python manage.py runserver
```

Visit:

- **Home:** http://127.0.0.1:8000/
- **Phases:** http://127.0.0.1:8000/phases/
- **Admin:** http://127.0.0.1:8000/admin/
- **API root:** http://127.0.0.1:8000/api/

## Sample Data

The `seed_data` command loads four lower mantle phases:

| Phase | Formula | Key data |
|-------|---------|----------|
| Bridgmanite | (Mg,Fe)SiO₃ | Pnma structure, BM EOS, PV/EV curves, elastic properties |
| Ferropericlase | (Mg,Fe)O | Fm-3m structure, Vinet EOS |
| Ca-perovskite | CaSiO₃ | Pbnm structure, DFT EOS |
| Post-perovskite | MgSiO₃ | Cmcm structure, two EOS entries for multi-series plots |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/phases/` | Phase list/create |
| `/api/sources/` | Literature sources |
| `/api/crystal-structures/` | Crystal structure data |
| `/api/eos-entries/` | EOS entries (with nested parameters, PV, EV) |
| `/api/eos-parameters/` | Individual EOS parameters |
| `/api/pv-data/` | Pressure–volume data points |
| `/api/ev-data/` | Energy–volume data points |
| `/api/elastic-measurements/` | Elastic/seismic properties |
| `/api/extraction-jobs/` | LLM extraction jobs |
| `/api/extracted-records/` | Staged extraction records |

All endpoints support search, ordering, and pagination.

Example:

```bash
curl http://127.0.0.1:8000/api/phases/?search=bridgmanite
curl http://127.0.0.1:8000/api/eos-entries/?search=Birch-Murnaghan
```

## Data Models

```
Phase ──┬── CrystalStructure ── Source
        ├── EOSEntry ──┬── EOSParameter
        │              ├── PVData
        │              └── EVData
        └── ElasticMeasurement ── Source

ExtractionJob ── ExtractedRecord (staging, not direct import)
```

LLM outputs are **never** written directly to scientific tables. They go to `ExtractedRecord` first; only reviewer-approved records are imported via the review workflow.

## Extraction Workflow

1. Upload a PDF at `/extraction/upload/`
2. Semantic extraction tasks run (source/phase, crystal structure, EOS, PV/EV, elastic)
3. Results appear as `ExtractedRecord` rows with validation status
4. Review each record at `/extraction/records/<id>/review/`
5. Approved records are validated and inserted into final tables

> **Note:** The included extraction service uses mock LLM responses for demonstration. Replace `minerals/services/extraction.py` with real API calls for production use.

## Project Structure

```
django_minerals/
├── manage.py
├── mantle_db/          # Project settings
├── minerals/
│   ├── models.py       # All 10 data models
│   ├── admin.py
│   ├── serializers.py
│   ├── viewsets.py     # DRF ViewSets + query helpers
│   ├── views.py        # Frontend views
│   ├── urls.py         # Web URLs
│   ├── api_urls.py     # API router
│   ├── forms.py
│   ├── validators.py   # Scientific validation rules
│   ├── services/
│   │   ├── extraction.py
│   │   └── import_approved.py
│   ├── templates/
│   ├── static/
│   └── management/commands/seed_data.py
└── requirements.txt
```

## Validation Rules

- Pressure must be positive; units: GPa, Pa, bar, kbar
- Temperature units: K, Celsius
- Volume must be positive
- Bulk modulus (K₀) and shear modulus must be positive
- DOI must match standard format
- EOS model from allowed set: Birch-Murnaghan, Vinet, Murnaghan, BM3, BM4, Holzapfel, Keane, other
- Unknown phase names flagged for review

## License

Academic/research use. Sample literature DOIs are representative placeholders for demonstration.

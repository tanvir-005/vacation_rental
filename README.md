# Vacation Rental Search Platform

A Django-based vacation rental discovery platform built with PostgreSQL, PostGIS, and pgvector. It supports geographic property search, natural-language semantic search, property management through Django Admin, and REST APIs for location autocomplete and property discovery.

## Features

- **Geographic search:** Find properties within a configurable radius of a destination using PostGIS.
- **Semantic search:** Describe your ideal stay in natural language and retrieve relevant properties using Sentence Transformers.
- **Hybrid search API:** Combine a semantic query with a geographic destination and search radius.
- **Location autocomplete:** Match destination prefixes and use vector similarity as a fallback.
- **Property listings:** Paginated results with property details, prices, amenities, and images.
- **Property details:** View descriptions, guest capacity, amenities, image galleries, and distance from a selected destination.
- **Django Admin:** Manage locations, properties, and property images, with filters, search, inline editing, and image previews.
- **Bulk data import:** Import property data from supported tabular file formats.
- **Vector indexing:** Use pgvector embeddings and HNSW indexes to support similarity search.
- **Automated tests:** Validate API behavior, query parameters, semantic search, and geographic filtering.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| Database | PostgreSQL |
| Geographic queries | PostGIS |
| Vector search | pgvector |
| Embeddings | Sentence Transformers |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| REST APIs | Django REST Framework |
| Data processing | Pandas |
| Environment and dependency management | `uv` |
| Containerization | Docker Compose |
| Frontend | Django templates, HTML, CSS |

## Architecture

The application uses Django for request handling, forms, templates, models, and administration. PostgreSQL stores the application data, while PostGIS performs geographic calculations and pgvector stores embeddings for semantic similarity search.

The Sentence Transformers model converts location names and property information into 384-dimensional vectors. The application uses cosine distance to rank semantically relevant results.

## Prerequisites

Install the following tools before running the project:

- Docker Engine
- Docker Compose
- Git
- `uv`

The application dependencies and database services are managed through the project configuration and Docker Compose.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/tanvir-005/vacation_rental.git
cd vacation_rental
```

### 2. Configure environment variables

Create a `.env` file in the project root using the variable names expected by `config/settings.py` and the database configuration in the Compose file.

Do not commit `.env` or place passwords, API keys, or other secrets in this README.

### 3. Start the application

```bash
docker compose up -d --build
```

Check the running services:

```bash
docker compose ps
```

### 4. Apply database migrations

```bash
docker compose exec web uv run python manage.py migrate
```

### 5. Create an administrator account

```bash
docker compose exec web uv run python manage.py createsuperuser
```

Follow the prompts to configure the account.

### 6. Open the application

- **Homepage:** http://localhost:8000/
- **Django Admin:** http://localhost:8000/admin/

## Data Import and Embedding Generation

The project includes a synthetic dataset of 2,000 vacation rental properties distributed across 10 destinations in Bangladesh. The dataset is intended for development, demonstration, and testing; it does not represent verified real-world rental listings.

The database has been populated with locations, properties, image references, geographic coordinates, and property embeddings.

If starting with an empty database, use the project's existing property-import management command and the supplied dataset. Run the command's help option to confirm its exact arguments:

```bash
docker compose exec web uv run python manage.py help
```

To generate or regenerate property embeddings, use the project's embedding management command. Check the command's help output for its exact name and options before running it.

The embedding model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

It generates 384-dimensional embeddings from property titles, destination names, addresses, descriptions, and amenities.

**Note:** The exact import command, dataset path, and embedding command should be documented from the current repository configuration.

## Search Modes

### Explore a Place

Search by destination and specify a radius in kilometers. PostGIS filters properties geographically, and results are ordered by distance from the selected destination.

### Find a Stay

Describe the desired accommodation in natural language, for example:

- A quiet cottage surrounded by nature
- An apartment in Dhaka with modern amenities
- A mountain cabin with scenic views
- A beachfront property with a sea view

The application embeds the query and ranks properties by cosine distance. Lower cosine distance indicates greater similarity.

## REST API

All endpoints use the application's local base URL:

```text
http://localhost:8000
```

### Location autocomplete

```http
GET /api/locations/autocomplete/?q=co&limit=5
```

Query parameters:

| Parameter | Description |
|---|---|
| `q` | Destination query; required |
| `limit` | Maximum results, from 1 to 20; defaults to 5 |

The endpoint returns matching locations, prioritizing exact and prefix matches before semantic fallback.

### Property search

```http
GET /api/properties/search/?q=quiet%20cottage&limit=10
```

Query parameters:

| Parameter | Description |
|---|---|
| `q` | Natural-language search query; required |
| `destination` | Optional geographic destination |
| `radius_km` | Geographic search radius; defaults to 20 km, maximum 500 km |
| `limit` | Maximum results; defaults to 20, maximum 100 |

Without a destination, the endpoint ranks properties by semantic similarity. When a destination is provided, geographic filtering is applied before semantic ranking.

Example hybrid search:

```http
GET /api/properties/search/?q=sea%20view%20apartment&destination=Cox%27s%20Bazar&radius_km=30&limit=10
```

Invalid query parameters are validated by serializers. A destination that cannot be matched to a location with coordinates returns an explanatory response with no results.

## Running Tests

Run the Django application checks:

```bash
docker compose exec web uv run python manage.py check
```

Run the automated tests for the rentals application:

```bash
docker compose exec web uv run python manage.py test rentals
```

Check whether model changes require new migrations:

```bash
docker compose exec web uv run python manage.py makemigrations --check --dry-run
```

## Project Structure

```text
vacation_rental/
├── config/
│   ├── settings.py
│   └── urls.py
├── rentals/
│   ├── management/
│   │   └── commands/
│   ├── services/
│   │   └── semantic_search.py
│   ├── templates/
│   │   └── rentals/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
├── data/
├── manage.py
├── pyproject.toml
├── uv.lock
├── REQUIREMENTS.md
└── README.md
```

This is a representative structure; verify file and directory names against the repository before delivery.

## Security and Deployment Notes

- Keep `.env` and other secret-bearing files out of version control.
- Uploaded media and generated datasets should be included in version control only when intentionally required for the demonstration.
- Configure production `DEBUG`, `ALLOWED_HOSTS`, database credentials, and secret keys appropriately before deployment.
- The included synthetic listings are demonstration data, not verified commercial listings.
- The Sentence Transformers model may need to be downloaded on the first run and may require internet access unless it is already cached.

## License

Add the license applicable to this project before redistributing it.
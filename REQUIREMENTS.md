# Vacation Rental Platform — Assignment Requirements

## 1. Objective

Build a vacation rental property platform using Django, PostgreSQL, PostGIS, and pgvector. The assignment is organized into three implementation days.

## 2. Required Technology Stack

- **Python environment and dependency management:** `uv`
- **Backend framework:** Django
- **API framework:** Django REST Framework (DRF)
- **Database:** PostgreSQL
- **Geospatial support:** GeoDjango and PostGIS
- **Vector storage and similarity search:** pgvector
- **Data processing and imports:** Pandas; support for CSV, Parquet, and Excel imports
- **Embeddings:** Sentence Transformers, model `all-MiniLM-L6-v2`
- **Image support:** Pillow
- **Frontend:** Django HTML templates, with forms and URL routing
- **Database deployment for development:** PostgreSQL in Docker

## 3. Functional Requirements

### 3.1 Location Management

- Create a `Location` model.
- Support location names and geographic/spatial data through GeoDjango.
- Store location-name embeddings in pgvector for semantic search.

### 3.2 Property Management

- Create a `Property` model.
- Represent property location using spatial fields.
- Support property search based on location.
- Show property listings and property details, including amenities.
- Display the distance from the relevant city/location on the property detail page.

### 3.3 Property Images

- Create a `PropertyImage` model.
- Support multiple images for a property.
- Support inline image uploads and image previews in Django Admin.

### 3.4 Data Import

- Import vacation-rental property data from CSV using Pandas.
- Provide custom Django management commands for data processing/import.
- Support bulk imports from CSV, Parquet, and Excel files.

### 3.5 Django Admin

- Configure the models in Django Admin.
- Add custom list filters.
- Support inline property-image uploads and image previews.

### 3.6 Search and Frontend

- Create a homepage with a search form.
- Implement location-based property search using PostGIS.
- Create a paginated property-listing page.
- Create property-detail pages with images and amenities.
- Display distance from the city/location on property details.

### 3.7 Semantic Search and API

- Generate embeddings for location names using Sentence Transformers `all-MiniLM-L6-v2`.
- Store embeddings in pgvector.
- Create and test an HNSW vector index.
- Implement semantic location search.
- Combine location-based search with semantic search.
- Build a location-autocomplete API using semantic search.
- Use DRF serializers for payload validation and implement DRF endpoints.

## 4. Three-Day Implementation Plan

### Day 1 — Setup and Data Foundation

1. Set up PostgreSQL with PostGIS and pgvector using Docker.
2. Configure Django to use PostgreSQL.
3. Create the `Location`, `Property`, and `PropertyImage` models.
4. Import vacation-rental properties from CSV using Pandas.
5. Configure Django Admin with filters, inline image uploads, and image previews.

### Day 2 — Search and Frontend

1. Create the homepage and search form.
2. Implement location-based property search.
3. Create a paginated property-listing page.
4. Create property-detail pages with images and amenities.
5. Show the distance from the city/location on property details.

### Day 3 — Semantic Search with AI

1. Integrate Sentence Transformers using `all-MiniLM-L6-v2`.
2. Generate location-name embeddings.
3. Store location embeddings in pgvector.
4. Add and test HNSW indexing.
5. Implement semantic location search.
6. Combine location and semantic search.
7. Build a semantic-search-based location-autocomplete API.

## 5. Evaluation Criteria

The completed project should demonstrate:

- PostgreSQL with both PostGIS and pgvector enabled.
- Django project and application configuration.
- Pandas data processing and manipulation.
- Custom Django management commands and automated bulk imports.
- Django Admin list filters and inline image uploads.
- Correct URL routing for pages and APIs.
- Django models with spatial fields and vector embeddings.
- Django views for request/response handling.
- Django forms with custom validation.
- PostGIS spatial queries, including examples such as `DWithin` and `Intersects`.
- pgvector similarity queries using cosine distance, L2 distance, or inner product.
- DRF serializers with payload validation and working API endpoints.
- HTML templates that render data and search results.
- Accurate spatial and vector-search logic and smooth integration between components.

## 6. Reference Material

- **pgvector:** https://github.com/pgvector/pgvector
- **PostGIS workshop:** https://postgis.net/workshops/
- **Sentence Transformers:** https://www.sbert.net/
- **pgvector search:** https://github.com/pgvector/pgvector
- **Homepage example:** https://www.rentbyowner.com/
- **Search example:** https://www.rentbyowner.com/refine?search=Destin,%20Florida,%20USA&order=1&ptOmit=4
- **Property detail example:** https://www.rentbyowner.com/property/king-s-castle-luxury-beach-escape-huge-private-pool-spa-6-seater-golf-cart/HA-12120219223

## 7. Scope Notes

This document records the requirements stated in the assignment file. Specific model fields, embedding dimensions, exact API routes, search-ranking rules, and source-data schema are not fully specified in that file; settle those design details during implementation rather than treating assumptions as assignment requirements.

# Backend Technical Documentation

## Overview
The backend architecture is serverless and event-driven, optimized for high throughput and reliable data ingestion from the automated scrapers.

## Tech Stack
- **Database**: Neon PostgreSQL (Serverless)
- **ORM**: Drizzle ORM
- **Queue/Ingestion**: Upstash QStash
- **Cache/Rate Limiting**: Upstash Redis
- **Scraper**: Python (Crawl4AI + BeautifulSoup4)

## Architecture
1. **Scraper Service**: A Python script runs daily via GitHub Actions. It extracts data from multiple sources and POSTs it to the Next.js ingestion API.
2. **Ingestion API**: Located at `/api/ingest`, this endpoint receives and validates news articles.
3. **Queueing**: For high-volume ingestion, the API can forward tasks to Upstash QStash for asynchronous processing.
4. **Database**: Articles are stored in Neon PostgreSQL. Drizzle ORM manages the schema and queries.

## Database Schema
The main table is `articles`:
- `id`: Unique identifier (string)
- `headline`: Title of the article (text)
- `summary`: Short description (text)
- `pub_date`: Publication timestamp
- `editor_name`: Credited editor or source team
- `source_name`: Original publication name
- `original_url`: Direct link to source
- `tags`: Array of strings for categorization
- `search_vector`: tsvector for PostgreSQL full-text search

## API Endpoints
### `POST /api/ingest`
Receives article data from the scraper.
- **Security**: In production, requests are signed by Upstash QStash.
- **Payload**: An array of article objects.

## Scraper Logic
- **Crawl4AI**: Used for complex sites that require JS execution or have bot detection.
- **BeautifulSoup**: Used for fast parsing of structured HTML.
- **Deduplication**: Uses `uuid5` based on the original URL to ensure stable IDs and prevent duplicate entries in the database.

## Scaling
- **Rate Limiting**: Upstash Redis is used to limit API hits and protect the database.
- **Read Replicas**: Neon can be scaled horizontally if read traffic increases significantly.

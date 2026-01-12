# AroTranslate

The first comprehensive translation system for Aromanian, an endangered Romance language spoken in the Balkans.

## Overview

AroTranslate provides bidirectional translation between **Aromanian (rup)**, **Romanian (ron)**, and **English (eng)**, along with intelligent orthography conversion between two Aromanian writing standards. The system includes a web-based user interface, REST API, and an annotation system for translation quality evaluation.

## Features

- **Multi-language Translation**: Aromanian ↔ Romanian ↔ English
- **Fast Neural Machine Translation**: Powered by CTranslate2 optimized models
- **Intelligent Orthography Conversion**: Statistical n-gram analysis for accurate diacritics conversion
- **Error Annotation System**: Collect and manage translation quality feedback
- **RESTful API**: Rate-limited endpoints with comprehensive error handling
- **Production Ready**: Dockerized deployment with Gunicorn + Gevent workers
- **Persistent Storage**: MongoDB for annotation management
- **Health Monitoring**: Built-in health check endpoints

## Project Structure

```
AroTranslate/
├── app.py                          # Main Flask application & API routes
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── start.sh                        # Production startup script (Gunicorn)
├── pull_and_deploy.sh             # Deployment automation script
├── Makefile                        # Build commands
│
├── docker/
│   └── Dockerfile                 # Production Docker image
│
├── docker-compose.yml             # Production deployment config
├── docker-compose_build.yml       # Development build config
│
├── models/
│   ├── __init__.py
│   └── annotation.py              # Annotation data model
│
├── services/
│   ├── translation_service.py     # Translation logic & text processing
│   └── db_repository.py           # MongoDB data access layer
│
├── utils/
│   ├── logger.py                  # Logging configuration
│   ├── resources.py               # Resource loading utilities
│   └── text_processing.py         # Orthography conversion utilities
│
├── resources/
│   ├── fuh.json                   # N-gram frequency data (schwa to ă)
│   ├── fah.json                   # N-gram frequency data (schwa to â)
│   └── cunia_diaro.csv            # Word-level orthography dictionary (30k+ words)
│
└── templates/
    ├── index.html                 # Main translator UI
    ├── about.html                 # About page
    └── admin_dashboard.html       # Admin annotation panel
```

## Technologies

### Backend
- **Flask 3.0.3** - Web framework
- **Python 3.11** - Programming language
- **Gunicorn + Gevent** - Production WSGI server with async workers
- **Flask-Limiter** - Rate limiting (50 requests/minute)
- **Flask-Talisman** - Optional HTTPS security enforcement

### Machine Learning / NLP
- **CTranslate2 4.6.0** - Fast inference for translation models (NLLB-rup-ron-eng-ct2-v2)
- **Transformers 4.56.2** - Tokenization and model utilities
- **spaCy 3.7.6** - Romanian language tokenization
- **Razdel 0.5.0** - Sentence segmentation
- **SentencePiece** - Subword tokenization

### Database & Caching
- **MongoDB** - Document database for annotations
- **Memcached** - Distributed memory caching for rate limiting
- **PyMongo** - MongoDB Python driver

### Data Processing
- **Pandas** - CSV/data handling for orthography resources

## Getting Started

### Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.11+ for local development

### Production Deployment

```bash
# Pull and start services
docker-compose up -d

# Or use the deployment script
./pull_and_deploy.sh
```

The application will be available at `http://localhost:5000`

### Development Setup

```bash
# Build and run development environment
docker-compose -f docker-compose_build.yml up --build

# Development server will run on port 5003
```

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export MONGODB_URI="mongodb://localhost:27017"
export MEMCACHED_URI="memcached://localhost:11211"

# Run Flask development server
python app.py
```

## API Documentation

### Translation Endpoint

Translate text between supported languages.

**Endpoint:** `POST /translate`

**Request Body:**
```json
{
  "input_text": "string",
  "input_language": "Aromanian|Romanian|English",
  "output_language": "Aromanian|Romanian|English"
}
```

**Response:**
```json
{
  "translated_text": "string",
  "translate_time": 0.123
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Bună ziua",
    "input_language": "Romanian",
    "output_language": "Aromanian"
  }'
```

### Diacritics Conversion Endpoint

Convert between two Aromanian orthography standards.

**Endpoint:** `POST /diacritics`

**Request Body:**
```json
{
  "orthography": "cunia|diaro",
  "text": "string"
}
```

**Response:**
```json
{
  "text": "string"
}
```

**Orthography Standards:**
- **DIARO standard**: Modern, diacritic-heavy (uses ă, â, ș, ț, ń, ľ, d̦)
- **Cunia standard**: Traditional ASCII-compatible (uses ã, sh, ts, nj, lj, dz)

**Example:**
```bash
curl -X POST http://localhost:5000/diacritics \
  -H "Content-Type: application/json" \
  -d '{
    "orthography": "cunia",
    "text": "Bună dzua"
  }'
```

### Annotation Endpoints

Manage translation quality annotations.

**Create Annotation:**
```
POST /annotations
Body: {
  "original_text": "string",
  "translated_text": "string",
  "annotations": [{"start": 0, "end": 5, "level": 1}]
}
```

**List Annotations:**
```
GET /annotations?limit=100&offset=0
```

**Get Single Annotation:**
```
GET /annotations/<id>
```

**Update Annotation:**
```
PATCH /annotations/<id>
Body: {
  "private_id": "uuid",
  "annotations": [{"start": 0, "end": 5, "level": 2}]
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "api": "operational",
  "mongodb": "connected"
}
```

## Language Support

| Language | Code | Native Names |
|----------|------|--------------|
| Aromanian | `rup` | Aromână, Armãnã |
| Romanian | `ron` | Română, Română |
| English | `eng` | Engleză, Inglezã |

## Configuration

Environment variables (configured in `config.py`):

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_LOAD_NAME` | Translation model name | NLLB-rup-ron-eng-ct2-v2 |
| `MAX_INPUT_TOKENS` | Input token limit | 1024 |
| `BATCH_SIZE` | Translation batch size | 4 |
| `MAX_OUTPUT_TOKENS` | Max output length | 1024 |
| `RATE_LIMIT` | Flask-Limiter rule | 50 per minute |
| `MEMCACHED_URI` | Caching backend URI | memcached://memcached:11211 |
| `TALISMAN` | HTTPS enforcement toggle | disabled |
| `MONGODB_URI` | Database connection | mongodb://mongodb:27017 |
| `MONGODB_DATABASE` | Database name | arotranslate |

## Orthography Conversion Details

The orthography conversion system uses a sophisticated approach:

1. **Word Dictionary Lookup** (`resources/cunia_diaro.csv`): 30,000+ pre-mapped words
2. **N-gram Frequency Analysis** (`resources/fuh.json`, `resources/fah.json`): Statistical resolution of ambiguous characters
3. **Consonant Mappings**: Special character transformations (sh→ș, ts→ț, nj→ń, lj→ľ, dz→d̦)

This ensures accurate conversion beyond simple character replacement, especially for the ambiguous "ã" character which can map to either "ă" or "â" depending on linguistic context.

## Architecture

### Core Components

1. **Main Application** (`app.py`): Flask routes, request validation, error handling
2. **Translation Service** (`services/translation_service.py`): CTranslate2 integration, batch processing
3. **Text Processing** (`utils/text_processing.py`): Orthography conversion algorithms
4. **Database Layer** (`services/db_repository.py`): MongoDB singleton repository pattern
5. **Annotation Model** (`models/annotation.py`): Data validation for error annotations

### Deployment Architecture

```
┌─────────────────┐
│   Nginx/Proxy   │
└────────┬────────┘
         │
┌────────▼────────┐
│  Gunicorn       │
│  (2 workers)    │
└────────┬────────┘
         │
┌────────▼────────┐     ┌──────────┐     ┌────────────┐
│  Flask App      │────▶│ MongoDB  │     │ Memcached  │
│  (Rate Limited) │     └──────────┘     └──────┬─────┘
└────────┬────────┘                             │
         │                                      │
         └──────────────────────────────────────┘
                  Rate Limit Storage
```

## Rate Limiting

All endpoints are rate-limited to **50 requests per minute** per IP address. Rate limit state is stored in Memcached for distributed environments.

## Error Handling

The application includes comprehensive error handling:
- Input validation (non-empty text, valid languages)
- Token limit checks (prevents OOM errors)
- MongoDB connection resilience (graceful degradation)
- HTTP error responses with descriptive messages
- Comprehensive logging with version tracking

## Contributing

When contributing to this project:
1. Maintain the existing code structure
2. Add tests for new features
3. Update documentation for API changes
4. Follow PEP 8 style guidelines
5. Ensure Docker builds succeed

## License

[Add your license information here]

## Acknowledgments

- Translation model based on Meta's **No Language Left Behind (NLLB)** project
- Aromanian orthography resources from linguistic research
- Built to support the preservation and modernization of the Aromanian language

## Contact

[Add contact information or links here]

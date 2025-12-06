# ETPS Backend

Backend API for the Enterprise-Grade Talent Positioning System (ETPS).

## Overview

FastAPI-based backend providing:
- Resume tailoring and generation
- Cover letter generation
- Job description parsing and skill-gap analysis
- Company intelligence (Phase 2)
- Networking suggestions (Phase 2)
- Application tracking (Phase 3)

## Tech Stack

- **Framework:** FastAPI (Python)
- **Database:** SQLite (Phase 1-2)
- **Vector Store:** Qdrant (local instance)
- **AI Models:** Claude Sonnet/Opus (primary), GPT-4o (fallback)

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── routers/             # API route handlers
├── services/            # Business logic
├── db/                  # Database models and configuration
├── config/              # Configuration files
└── requirements.txt     # Python dependencies
```

## Getting Started

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload
```

## API Endpoints

- `GET /health` - Health check endpoint

TODO: Additional endpoints will be documented as implemented.

## Configuration

Configuration is managed via:
- Environment variables for secrets (API keys)
- `config/config.yaml` for application settings

## License

Proprietary - Benjamin Black

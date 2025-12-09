# ETPS Backend

Backend API for the Enterprise-Grade Talent Positioning System (ETPS).

**Version:** 0.1.0
**Tests:** 711 passing
**Phase Status:** Phase 1A-1B Complete, Phase 1C (Deployment) in progress

## Overview

FastAPI-based backend providing:
- Resume tailoring and generation
- Cover letter generation with critic loop
- Job description parsing and skill-gap analysis
- Company intelligence (industry, culture, AI maturity)
- Capability cluster extraction
- Learning from approved outputs

## Tech Stack

- **Framework:** FastAPI (Python 3.13)
- **Database:** SQLite (dev), PostgreSQL (production)
- **Vector Store:** Qdrant (local or cloud)
- **AI Models:** Claude Sonnet/Opus (primary), GPT-4o (fallback)
- **Embeddings:** OpenAI text-embedding-3-small (384-dim)

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── routers/             # API route handlers
│   ├── job.py           # JD parsing, skill-gap analysis
│   ├── resume.py        # Resume generation, DOCX export
│   ├── cover_letter.py  # Cover letter generation
│   ├── company.py       # Company profile enrichment
│   ├── capability.py    # Capability cluster extraction
│   ├── critic.py        # Quality evaluation
│   ├── outputs.py       # Approved output learning
│   └── users.py         # User profile endpoints
├── services/            # Business logic
│   ├── resume_tailor.py # Main orchestrator
│   ├── cover_letter.py  # Cover letter generation
│   ├── skill_gap.py     # Semantic skill matching
│   ├── bullet_rewriter.py  # LLM bullet optimization
│   ├── summary_rewrite.py  # Summary generation
│   ├── critic.py        # Quality evaluation
│   ├── pagination.py    # Layout simulation
│   ├── company_enrichment.py  # Company intelligence
│   ├── capability_extractor.py  # Capability clusters
│   ├── vector_store.py  # Qdrant integration
│   └── llm/             # LLM abstraction layer
│       ├── base.py      # Abstract interface
│       ├── mock_llm.py  # Testing without API
│       └── claude_llm.py  # Claude API integration
├── db/                  # Database models and configuration
│   ├── models.py        # SQLAlchemy models
│   └── database.py      # Session management
├── schemas/             # Pydantic request/response schemas
├── config/              # Configuration files
│   └── config.yaml      # Application settings
├── tests/               # Test suite (711 tests)
└── requirements.txt     # Python dependencies
```

## Getting Started

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-...  # For production LLM
export OPENAI_API_KEY=sk-...          # For embeddings

# Run development server
uvicorn main:app --reload --port 8000
```

## API Reference

Base URL: `http://localhost:8000/api/v1`

### Health Check

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check with version info |

### Job Endpoints (`/job`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/parse` | Parse JD text/URL into structured JobProfile |
| POST | `/skill-gap` | Analyze skill gaps between user and job |
| PUT | `/job-profiles/{id}/skills` | Update skill selection/ordering |
| GET | `/job-profiles/{id}/skills` | Get skill selection state |

**POST /parse Request:**
```json
{
  "jd_text": "Full job description text...",
  "jd_url": null,
  "user_id": 1
}
```

**POST /skill-gap Request:**
```json
{
  "job_profile_id": 1,
  "user_id": 1
}
```

### Resume Endpoints (`/resume`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate tailored resume JSON |
| POST | `/docx` | Generate resume as DOCX download |
| GET | `/bullets/{id}/versions` | Get bullet version history |

**POST /generate Request:**
```json
{
  "job_profile_id": 1,
  "user_id": 1,
  "max_bullets_per_role": 4,
  "max_skills": 12,
  "custom_instructions": null
}
```

### Cover Letter Endpoints (`/cover-letter`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate cover letter JSON |
| POST | `/docx` | Generate cover letter as DOCX download |
| POST | `/text` | Generate cover letter as plain text |

**POST /generate Request:**
```json
{
  "job_profile_id": 1,
  "user_id": 1,
  "company_profile_id": null,
  "context_notes": "Met John at XYZ conference",
  "referral_name": null
}
```

### Company Endpoints (`/company`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/enrich` | Enrich company profile with industry/culture/AI data |

**POST /enrich Request:**
```json
{
  "company_name": "Acme Corp",
  "jd_text": "Job description for context...",
  "website_url": "https://acme.com",
  "user_id": 1
}
```

### Capability Endpoints (`/capability`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/clusters/{job_profile_id}` | Get capability clusters for job |
| POST | `/extract` | Extract capabilities from JD text |
| PUT | `/clusters/{job_profile_id}` | Update/cache capability clusters |
| GET | `/user-skills/{user_id}` | Get user's extracted skills |
| POST | `/user-skills/{user_id}` | Extract skills from user profile |

### Critic Endpoints (`/critic`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/evaluate` | Evaluate content quality |

### Outputs Endpoints (`/outputs`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/approve` | Mark output as approved (for learning) |
| GET | `/similar` | Find similar approved outputs |

### Users Endpoints (`/users`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/{user_id}` | Get user profile and candidate info |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes (prod) | Claude API key for LLM |
| `OPENAI_API_KEY` | Yes | OpenAI API key for embeddings |
| `DATABASE_URL` | No | Database connection (default: SQLite) |
| `QDRANT_URL` | No | Vector store URL (default: localhost:6333) |

### config.yaml

```yaml
app:
  name: "ETPS"
  version: "0.1.0"
  environment: "development"

models:
  premium_model: "claude-sonnet-4"
  fallback_model: "gpt-4o"
  embedding_model: "text-embedding-3-small"

critic:
  max_iterations: 3
  ats_score_threshold: 75

pagination:
  page1_line_budget: 50
  page2_line_budget: 55
  chars_per_line_estimate: 75
```

## Testing

```bash
# Run all tests
cd backend && python -m pytest -v

# Run specific test file
python -m pytest tests/test_resume_tailor.py -v

# Run with coverage
python -m pytest --cov=services --cov-report=html
```

## LLM Selection

The system automatically selects the appropriate LLM:

- **Production (ANTHROPIC_API_KEY set):** Uses Claude via `ClaudeLLM`
- **Development (no API key):** Uses `MockLLM` for deterministic testing

```python
from services.llm import create_llm

llm = create_llm()  # Auto-selects based on environment
```

## Phase Roadmap

```
Phase 1A: Core Quality (Sprints 1-10)           COMPLETE
Phase 1B: Company Enrichment (Sprints 11-12)    COMPLETE
Phase 1C: Deployment (Sprints 13-14)            TARGET
  - Sprint 13: Portfolio Security
  - Sprint 14: Cloud Deployment (Railway + Vercel)
Phase 2:  Networking (Sprints 15-17)            NOT STARTED
Phase 3:  Application Tracking (Sprints 18+)    DEFERRED
```

## License

Proprietary - Benjamin Black

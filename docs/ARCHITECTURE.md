# ETPS Architecture Overview

**Version:** 2.0
**Last Updated:** December 2025

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Frontend (Next.js + shadcn/ui)                │
│                     Phase 1A-1B COMPLETE                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Job Intake  │  │  Generate   │  │   Results   │             │
│  │    Form     │  │   Buttons   │  │    Panel    │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         └────────────────┼────────────────┘                     │
└──────────────────────────┼──────────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ /api/v1/job │  │/api/v1/resume│  │/api/v1/     │              │
│  │   (parse,   │  │  (generate, │  │cover-letter │              │
│  │  skill-gap) │  │   docx)     │  │  (generate) │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐              │
│  │/api/v1/     │  │/api/v1/     │  │/api/v1/     │              │
│  │ company     │  │ capability  │  │  critic     │              │
│  │  (enrich)   │  │ (clusters)  │  │ (evaluate)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                              │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  resume_tailor   │───▶│    skill_gap     │                   │
│  │  (orchestrator)  │    │   (analysis)     │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ bullet_rewriter  │    │   embeddings     │                   │
│  │ summary_rewrite  │    │  (OpenAI API)    │                   │
│  │ portfolio_loader │    │                  │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │     critic       │    │   vector_store   │                   │
│  │ (quality eval)   │    │    (Qdrant)      │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   pagination     │    │  cover_letter    │                   │
│  │ (layout sim)     │    │   (generator)    │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │capability_extract│    │company_enrichment│                   │
│  │ evidence_mapper  │    │ (industry, AI    │                   │
│  │ cluster_cache    │    │  maturity)       │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
│  ┌──────────────────┐                                           │
│  │   llm/           │                                           │
│  │   - base.py      │  Auto-selects based on ANTHROPIC_API_KEY  │
│  │   - mock_llm.py  │  MockLLM for testing without API costs    │
│  │   - claude_llm.py│  ClaudeLLM for production quality         │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   PostgreSQL     │    │     Qdrant       │                   │
│  │  (Railway prod)  │    │   (vectors)      │                   │
│  │  SQLite (dev)    │    │                  │                   │
│  │                  │    │                  │                   │
│  │  - Users         │    │  - Bullet embeds │                   │
│  │  - Experiences   │    │  - Job embeds    │                   │
│  │  - Engagements   │    │  - Approved out  │                   │
│  │  - Bullets       │    │                  │                   │
│  │  - JobProfiles   │    │                  │                   │
│  │  - CompanyProfiles│   │                  │                   │
│  │  - Applications  │    │                  │                   │
│  │  - ApprovedOutput│    │                  │                   │
│  └──────────────────┘    └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Job Endpoints (`/api/v1/job`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/parse` | Parse JD text/URL into structured JobProfile |
| POST | `/skill-gap` | Analyze skill gaps between user and job |
| PUT | `/job-profiles/{id}/skills` | Update skill selection/ordering |
| GET | `/job-profiles/{id}/skills` | Get skill selection state |

### Resume Endpoints (`/api/v1/resume`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate tailored resume JSON |
| POST | `/docx` | Generate resume as DOCX download |
| GET | `/bullets/{id}/versions` | Get bullet version history |

### Cover Letter Endpoints (`/api/v1/cover-letter`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate cover letter JSON |
| POST | `/docx` | Generate cover letter as DOCX download |
| POST | `/text` | Generate cover letter as plain text |

### Company Endpoints (`/api/v1/company`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/enrich` | Enrich company profile with industry/culture/AI data |

### Capability Endpoints (`/api/v1/capability`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/clusters/{job_profile_id}` | Get capability clusters for job |
| POST | `/extract` | Extract capabilities from JD text |
| PUT | `/clusters/{job_profile_id}` | Update/cache capability clusters |
| GET | `/user-skills/{user_id}` | Get user's extracted skills |
| POST | `/user-skills/{user_id}` | Extract skills from user profile |

### Critic Endpoints (`/api/v1/critic`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/evaluate` | Evaluate content quality |

### Outputs Endpoints (`/api/v1/outputs`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/approve` | Mark output as approved (for learning) |
| GET | `/similar` | Find similar approved outputs |

### Users Endpoints (`/api/v1/users`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/{user_id}` | Get user profile |

---

## Core Data Flow

### Resume Generation Pipeline (PRD 1.6)

```
1. Job Intake
   └── Parse JD (text or URL) → JobProfile
   └── Validate extraction quality
   └── Extract capability clusters

2. Company Enrichment (optional)
   └── Infer industry, size, culture
   └── Assess data/AI maturity

3. Skill-Gap Analysis
   └── Compare user skills vs JD requirements
   └── Generate positioning strategies
   └── Semantic similarity via embeddings

4. Bullet Selection
   └── Score bullets by relevance
   └── Apply pagination constraints
   └── Optional: Rewrite for keywords

5. Summary Generation
   └── Generate tailored summary
   └── Enforce word/line limits

6. Critic Loop (max 3 iterations)
   └── Evaluate quality scores
   └── Check truthfulness
   └── Verify ATS compliance
   └── Adjust if needed

7. Output
   └── JSON structure
   └── Plain text rendering
   └── DOCX (preserves template formatting)
```

---

## Service Responsibilities

### resume_tailor.py (Orchestrator)
- Main entry point for resume generation
- Coordinates all other services
- Handles pagination-aware allocation
- Returns `TailoredResume` schema

### skill_gap.py
- Semantic skill matching using embeddings
- Identifies matched skills, gaps, weak signals
- Generates positioning strategies
- Uses Qdrant for similarity search

### bullet_rewriter.py
- LLM-powered bullet optimization
- Keyword integration from JD
- STAR enrichment
- Compression for space constraints
- Version history tracking

### summary_rewrite.py
- Professional summary generation
- Candidate profile integration
- Word/line limit enforcement
- Banned phrase removal

### critic.py
- Quality evaluation (alignment, clarity, impact, tone)
- ATS keyword scoring
- Truthfulness validation
- Em-dash and banned phrase detection
- Pagination constraint checking

### pagination.py
- Line budget estimation
- Value-per-line prioritization
- Page split simulation
- Orphan header detection
- Bullet compression

### cover_letter.py
- Cover letter generation with critic loop
- Paragraph structure (hook, body, close)
- Style guide enforcement
- Requirement coverage tracking

### company_enrichment.py
- Company profile creation/update
- Industry and size inference
- Culture signals extraction
- Data/AI maturity assessment

### capability_extractor.py
- LLM-based capability cluster extraction
- Evidence mapping from JD text
- Cluster caching for performance

### skills_formatter.py
- LLM-powered skills categorization
- Hallucination prevention via whitelist validation
- Fallback to keyword-based categorization
- Returns skills grouped by category (AI/ML, Programming, Cloud, etc.)

### vector_store.py
- Qdrant integration
- Bullet/job indexing
- Semantic search
- Similar output retrieval

### llm/ (LLM Layer)
- `base.py` - Abstract interface
- `mock_llm.py` - Template-based for testing
- `claude_llm.py` - Claude API integration
- `create_llm()` - Factory auto-selects based on `ANTHROPIC_API_KEY`

---

## Database Schema (v1.4.2)

```
User
├── id, email, name
├── candidate_profile (JSON)
└── Experiences[]
    ├── employer_name, job_title, dates
    ├── Engagements[] (consulting roles)
    │   └── Bullets[]
    └── Bullets[] (direct roles)

JobProfile
├── id, user_id
├── job_title, company_name, seniority
├── extracted_skills[], must_have[], nice_to_have[]
├── core_priorities[], culture_keywords[]
├── selected_skills[], key_skills[]
├── capability_clusters[], capability_cluster_cache_key
└── embedding (384-dim vector)

CompanyProfile
├── id, name, website
├── industry, size_band, headquarters
├── business_lines, known_initiatives
├── culture_signals[], data_ai_maturity
└── embedding (384-dim vector)

Application
├── id, user_id, job_profile_id
├── status, ats_score
├── resume_json, cover_letter_json
└── critic_scores (JSON)

ApprovedOutput
├── id, user_id
├── output_type (bullet, summary, paragraph)
├── content, quality_score
└── embedding (384-dim vector)
```

---

## Configuration

### config.yaml Structure
```yaml
app:
  name, version, environment

models:
  premium_model: claude-sonnet-4
  fallback_model: gpt-4o
  embedding_model: text-embedding-3-small

critic:
  max_iterations: 3
  ats_score_threshold: 75

pagination:
  page1_line_budget: 50
  page2_line_budget: 55
  chars_per_line_estimate: 75
  compression_enabled: true
```

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...   # Enables Claude LLM (required for production)
OPENAI_API_KEY=sk-...          # For embeddings
DATABASE_URL=sqlite:///...      # Database connection (PostgreSQL in production)
QDRANT_URL=http://localhost:6333  # Vector store
```

---

## Security Considerations

### Input Validation
- All API parameters bounds-checked
- String lengths limited
- Regex patterns pre-compiled with length limits
- Request body size limits (Sprint 13)

### Data Protection
- API keys in environment variables only
- No secrets in code or logs
- User data isolated by user_id
- PII handling via Contact table (pseudonymous IDs elsewhere)

### Error Handling
- Specific exception types
- Sanitized error messages (no stack traces in production)
- Full tracebacks in development only

### Planned Security (Sprint 13)
- Rate limiting (10 req/min for generation)
- CORS restriction to production domains
- SSRF prevention in URL fetch
- Security headers (CSP, X-Frame-Options)

---

## Testing Strategy

### Unit Tests (783 total - December 2025)
- Service-level tests
- Mock LLM for deterministic results
- Mock vector store for speed
- Real LLM integration via ClaudeLLM

### Test Files
- `test_pagination_allocation.py` - Pagination service
- `test_sprint_8c_regression.py` - Integration tests
- `test_bullet_rewriter.py` - Bullet operations
- `test_critic.py` - Quality evaluation
- `test_skill_gap.py` - Skill analysis
- `test_vector_store.py` - Qdrant operations
- `test_capability_clusters.py` - Capability extraction
- `test_skill_selection.py` - Interactive skill selection
- `test_job_parser_extraction.py` - JD parsing quality
- `test_company_enrichment.py` - Company profile enrichment
- `test_skills_formatter.py` - Skills categorization and validation

---

## Deployment

### Development
- SQLite database (default, via `DATABASE_URL` env fallback)
- Mock vector store option
- Local Qdrant container
- Both localhost:3000 (frontend) and localhost:8000 (backend)

### Production (Sprint 14 - COMPLETE)
- **Backend:** Railway (https://etps-production.up.railway.app)
- **Frontend:** Vercel (https://etps.benjaminblack.consulting)
- **Database:** PostgreSQL (Railway addon)
- **Vector Store:** Qdrant Cloud (free tier)
- **Auto-deploy:** Git push triggers Railway/Vercel deployments

### Database Configuration
```python
# db/database.py - auto-selects based on DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./etps.db")
# Handles Railway's postgres:// → postgresql:// conversion for SQLAlchemy 2.0
```

### Rate Limiting
- slowapi middleware requires `request: Request` parameter naming
- 10 requests/minute for generation endpoints
- 60 requests/minute for read endpoints

---

## Phase Roadmap

```
Phase 1A: Core Quality (Sprints 1-10)           COMPLETE
Phase 1B: Company Enrichment (Sprints 11-12)    COMPLETE
Phase 1C: Deployment (Sprints 13-14)            COMPLETE (Dec 2025)
Phase 2:  Networking (Sprints 15-17)            NOT STARTED
Phase 3:  Application Tracking (Sprints 18+)    DEFERRED
```

**Live URLs:**
- Frontend: https://etps.benjaminblack.consulting
- Backend: https://etps-production.up.railway.app

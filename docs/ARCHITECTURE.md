# ETPS Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│                    (Sprint 9-10 - Planned)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   /resume   │  │ /cover-letter│  │   /jobs     │              │
│  │   endpoints │  │  endpoints  │  │  endpoints  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
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
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │     SQLite       │    │     Qdrant       │                   │
│  │  (relational)    │    │   (vectors)      │                   │
│  │                  │    │                  │                   │
│  │  - Users         │    │  - Bullet embeds │                   │
│  │  - Experiences   │    │  - Job embeds    │                   │
│  │  - Bullets       │    │  - Approved out  │                   │
│  │  - JobProfiles   │    │                  │                   │
│  │  - Applications  │    │                  │                   │
│  └──────────────────┘    └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Data Flow

### Resume Generation Pipeline (PRD 1.6)

```
1. Job Intake
   └── Parse JD → JobProfile

2. Skill-Gap Analysis
   └── Compare user skills vs JD requirements
   └── Generate positioning angles

3. Bullet Selection
   └── Score bullets by relevance
   └── Apply pagination constraints
   └── Optional: Rewrite for keywords

4. Summary Generation
   └── Generate tailored summary
   └── Enforce word/line limits

5. Critic Loop (max 3 iterations)
   └── Evaluate quality scores
   └── Check truthfulness
   └── Verify ATS compliance
   └── Adjust if needed

6. Output
   └── JSON structure
   └── Plain text rendering
   └── (Future: PDF/DOCX)
```

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
- Cover letter generation
- Paragraph structure (hook, body, close)
- Critic loop integration
- Style guide enforcement

### vector_store.py
- Qdrant integration
- Bullet/job indexing
- Semantic search
- Similar output retrieval

## Database Schema (v1.3.0)

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

## Security Considerations

### Input Validation
- All API parameters bounds-checked
- String lengths limited
- Regex patterns pre-compiled with length limits

### Data Protection
- API keys in environment variables only
- No secrets in code or logs
- User data isolated by user_id

### Error Handling
- Specific exception types
- Full tracebacks for debugging
- No sensitive data in error messages

## Testing Strategy

### Unit Tests (344 total)
- Service-level tests
- Mock LLM for deterministic results
- Mock vector store for speed

### Integration Tests
- Cross-service workflows
- Database operations
- API endpoints (future)

### Test Files
- `test_pagination_allocation.py` - Pagination service
- `test_sprint_8c_regression.py` - Integration tests
- `test_bullet_rewriter.py` - Bullet operations
- `test_critic.py` - Quality evaluation
- `test_skill_gap.py` - Skill analysis
- `test_vector_store.py` - Qdrant operations

## Deployment (Planned - Sprint 19)

### Development
- SQLite database
- Mock vector store option
- Local Qdrant container

### Production
- PostgreSQL database
- Qdrant Cloud
- Railway (backend)
- Vercel (frontend)

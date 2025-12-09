# ETPS Implementation Plan
**Sprint Roadmap & Current Status**
**Version 2.0 - December 2025**

---

## Current Status

**Completed:** Phase 1 (Core Quality, Schema, LLM Enhancement, Vector Search, Frontend MVP) + Sprint 12 (Company Enrichment)

**Next Up:** Sprint 13B (Portfolio Security) -> Sprint 14 (Cloud Deployment)

**Tests:** 711 passing

> For detailed task lists and implementation notes from completed sprints, see `docs/archive/COMPLETED_SPRINTS.md`

---

## Progress Summary

| Sprint | Status | Notes |
|--------|--------|-------|
| Sprints 1-12 | Done | Core Quality, Schema, LLM, Vector Search, Frontend, Company Enrichment |
| Sprint 13: Hiring Manager Inference | Not Started | JD parsing for reporting structure |
| **Sprint 13B: Portfolio Security** | **Not Started** | **Minimum security for public demo** |
| **Sprint 14: Cloud Deployment** | **Not Started** | **Railway + Vercel deployment** |
| Sprint 15+: Future Enhancements | Deferred | Networking, Application Tracking, Full Auth |

---

## Phase Overview

```
Phase 1: Core Quality (Sprints 1-12)                    COMPLETE
  - Resume/Cover Letter Critic & ATS Scoring
  - Skill-Gap Analysis with Semantic Matching
  - Schema Migration (v1.3.0 with engagements)
  - Bullet Rewriting & Summary Rewrite Engine
  - Qdrant Vector Search & Learning System
  - Pagination-Aware Layout
  - Frontend MVP (Next.js + Job Intake UI)
  - Capability-Aware Skill Extraction
  - Company Profile Enrichment

Phase 2B: Portfolio Deployment (Sprints 13B-14)         TARGET
  - Portfolio Security Hardening
  - Cloud Deployment (Railway + Vercel)

Phase 3+: Future Enhancements                           DEFERRED
  - Hiring Manager Inference
  - Warm Contact Identification
  - Application Status Tracking
  - Full Authentication
```

---

## Sprint 13B: Portfolio Security Hardening

**Goal:** Implement minimum security measures required for safe public portfolio deployment.

**Status:** Not Started

### Tasks

| ID | Task | Severity | Est. |
|----|------|----------|------|
| 13B.1 | Implement rate limiting middleware | HIGH | 2h |
| 13B.2 | Restrict CORS to production domain only | CRITICAL | 30m |
| 13B.3 | Add SSRF prevention to URL fetch | HIGH | 3h |
| 13B.4 | Add request body size limits | HIGH | 1h |
| 13B.5 | Sanitize error messages (no stack traces) | HIGH | 2h |
| 13B.6 | Configure secrets in Railway/Vercel env | CRITICAL | 1h |
| 13B.7 | Add security headers (CSP, X-Frame-Options) | MEDIUM | 1h |
| 13B.8 | Add health check with version info | LOW | 30m |

### Implementation Notes

**Rate Limiting:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
# 10 requests/minute for generation, 60/minute for reads
```

**CORS Restriction:**
```python
ALLOWED_ORIGINS = [
    "https://etps.benjaminblack.ai",  # Production
    "http://localhost:3000",           # Development
]
```

**Request Body Limits:**
```python
class JobParseRequest(BaseModel):
    jd_text: Optional[str] = Field(None, max_length=50000)
    jd_url: Optional[str] = Field(None, max_length=2000)
```

### Acceptance Criteria

- [ ] Rate limiting prevents >10 generation requests/minute per IP
- [ ] CORS rejects requests from unauthorized origins
- [ ] URL fetch blocks internal IPs and metadata endpoints
- [ ] Request payloads limited to reasonable sizes
- [ ] Error responses contain no stack traces or internal paths
- [ ] Security scan (bandit -ll) passes with no high-severity issues

**Estimated Effort:** 11 hours

---

## Sprint 14: Cloud Deployment

**Goal:** Deploy ETPS to Railway (backend) and Vercel (frontend) for public portfolio access.

**Status:** Not Started

**Prerequisite:** Sprint 13B (Portfolio Security) must be complete.

### Tasks

| ID | Task | Priority | Est. |
|----|------|----------|------|
| **Backend (Railway)** | | | |
| 14.1 | Create Railway project | P0 | 30m |
| 14.2 | Configure Procfile/railway.toml | P0 | 1h |
| 14.3 | Set up environment variables | P0 | 1h |
| 14.4 | Configure PostgreSQL (Railway addon) | P0 | 2h |
| 14.5 | Configure Qdrant Cloud or Railway addon | P1 | 2h |
| 14.6 | Test backend deployment | P0 | 1h |
| **Frontend (Vercel)** | | | |
| 14.7 | Create Vercel project | P0 | 30m |
| 14.8 | Configure vercel.json | P0 | 30m |
| 14.9 | Set up environment variables | P0 | 30m |
| 14.10 | Configure custom domain (optional) | P2 | 1h |
| 14.11 | Test frontend deployment | P0 | 1h |
| **Integration** | | | |
| 14.12 | Configure production CORS | P0 | 30m |
| 14.13 | Verify end-to-end flow | P0 | 2h |
| 14.14 | Write deployment documentation | P1 | 2h |

### Environment Variables

**Railway (Backend):**
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
QDRANT_URL=https://...
ENVIRONMENT=production
ALLOWED_ORIGINS=https://etps.benjaminblack.ai
```

**Vercel (Frontend):**
```
NEXT_PUBLIC_API_URL=https://etps-backend.up.railway.app
NEXT_PUBLIC_USER_NAME=Benjamin Black
```

### Acceptance Criteria

- [ ] Backend accessible at Railway URL
- [ ] Frontend accessible at Vercel URL
- [ ] All API endpoints functional in production
- [ ] Resume/cover letter generation works end-to-end
- [ ] DOCX downloads work correctly
- [ ] No CORS errors in browser console
- [ ] Site loads in <3 seconds

**Estimated Effort:** 16.5 hours

### Cost Estimates (Monthly)

| Service | Est. Cost |
|---------|-----------|
| Railway | $5-10 |
| Vercel | Free |
| Qdrant Cloud | Free (1GB) |
| Anthropic API | ~$10-20 |
| OpenAI API | ~$5 |
| **Total** | **~$20-35/month** |

---

## Deferred Sprints (Post-Deployment)

### Sprint 13: Hiring Manager Inference (PRD 5.3)

Extract reporting hints from JD, parse team keywords, score and rank hiring manager candidates with confidence levels.

### Sprint 15+: Networking & Application Tracking

- Warm Contact Identification (shared schools, employers, industries)
- Networking Output Generation (contact lists, outreach messages)
- Application Status Tracking
- Contact Management & Tasks

### Sprint 18: Full Production Hardening

JWT authentication, ownership validation, CSRF protection, audit logging - required only for multi-user deployment.

---

## Git Workflow

**Repository:** https://github.com/blackbenjamin/etps

**Commit Convention:**
- Sprint complete: `feat(sprint-N): <summary>`
- Bug fix: `fix: <summary>`
- Docs: `docs: <summary>`

**Pre-Push Checklist:**
```bash
cd backend
python -m pytest -v --tb=short     # All tests pass
bandit -r . -ll --exclude ./test*  # Security scan
```

---

## Test Coverage

- **Total Tests:** 711 passing
- **Coverage:** All Sprint 1-12 functionality tested
- **Key Test Files:** test_bullet_rewriter.py, test_truthfulness_check.py, test_summary_rewrite.py, test_text_output.py, test_vector_store.py, test_approved_outputs.py, test_pagination_allocation.py, test_job_parser_extraction.py, test_skill_selection.py, test_capability_clusters.py, test_company_enrichment.py

---

## Dependencies

### External
- Anthropic API Key (Claude LLM)
- OpenAI API Key (embeddings)
- Qdrant (vector store)

### Sprint Dependencies
```
Sprint 13B (Security) -> Sprint 14 (Deployment)
```

---

## Success Metrics

### Phase 1 (Complete)
- Resume generation < 60 seconds
- ATS score > 75 for all outputs
- Zero banned phrases in outputs
- Skill-gap analysis accurate and actionable

### Phase 2B (Target)
- Deployed and accessible via public URL
- All generation flows work end-to-end
- Security scan passes

---

*Last Updated: December 2025*
*For completed sprint details: `docs/archive/COMPLETED_SPRINTS.md`*

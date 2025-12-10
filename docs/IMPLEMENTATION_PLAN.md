# ETPS Implementation Plan
**Sprint Roadmap & Current Status**
**Version 2.1 - December 2025**

---

## Current Status

**Completed:** Phase 1A + Phase 1B + Phase 1C (Sprints 1-14)

**Live URLs:**
- Frontend: https://etps.benjaminblack.consulting
- Backend: https://etps-production.up.railway.app

**Next Up:** Phase 2 - Company Intelligence & Networking (Sprints 15-17)

**Tests:** 753 passing

> For detailed task lists and implementation notes from completed sprints, see `docs/archive/COMPLETED_SPRINTS.md`

---

## Progress Summary

| Sprint | Phase | Status | Notes |
|--------|-------|--------|-------|
| Sprints 1-10 | Phase 1A | Done | Core Quality, Schema, LLM, Vector Search, Frontend MVP |
| Sprints 11-12 | Phase 1B | Done | Company Profile Enrichment |
| Sprint 13: Portfolio Security | Phase 1C | Done | Rate limiting, CORS, SSRF prevention, security headers |
| **Sprint 14: Cloud Deployment** | **Phase 1C** | **Done** | **Railway + Vercel deployment** |
| Sprints 15-17: Company Intelligence | Phase 2 | Not Started | Hiring Manager Inference, Warm Contacts, Outreach |
| Sprints 18+: Application Tracking | Phase 3 | Deferred | Tracking, Reminders, Full Auth |

---

## Phase Overview (Aligned with PRD Section 7.2)

```
Phase 1: Core (Sprints 1-14)                            COMPLETE
  Phase 1A: Core Quality (Sprints 1-10)                 COMPLETE
    - Resume Tailoring & Cover Letter Generation
    - Critic Agent & ATS Scoring
    - Skill-Gap Analysis with Semantic Matching
    - Schema Migration (v1.3.0 with engagements)
    - Bullet Rewriting & Summary Rewrite Engine
    - Qdrant Vector Search & Learning System
    - Pagination-Aware Layout
    - Frontend MVP (Next.js + Job Intake UI)
    - Capability-Aware Skill Extraction

  Phase 1B: Company Enrichment (Sprints 11-12)          COMPLETE
    - Company Profile Enrichment from JD
    - Industry/Size/Culture Inference

  Phase 1C: Deployment (Sprints 13-14)                  COMPLETE
    - Portfolio Security Hardening (Sprint 13)
    - Cloud Deployment - Railway + Vercel (Sprint 14)
    - Live at: https://etps.benjaminblack.consulting

Phase 2: Company Intelligence & Networking (Sprints 15-17)  NOT STARTED
  - Hiring Manager Inference (PRD 5.3)
  - Warm Contact Identification (PRD 5.4)
  - Networking Suggestions & Outreach Drafts (PRD 5.5-5.6)

Phase 3: Application Tracking & Workflows (Sprints 18+)     DEFERRED
  - Application Status Tracking (PRD 5.8)
  - Contact Management & Tasks
  - Calendar/Email Integration
  - Interview Prep Modules
  - Full Authentication (multi-user)
```

---

## Sprint 13: Portfolio Security Hardening

**Goal:** Implement minimum security measures required for safe public portfolio deployment.

**Status:** COMPLETE (December 2025)

### Tasks

| ID | Task | Severity | Est. |
|----|------|----------|------|
| 13.1 | Implement rate limiting middleware | HIGH | 2h |
| 13.2 | Restrict CORS to production domain only | CRITICAL | 30m |
| 13.3 | Add SSRF prevention to URL fetch | HIGH | 3h |
| 13.4 | Add request body size limits | HIGH | 1h |
| 13.5 | Sanitize error messages (no stack traces) | HIGH | 2h |
| 13.6 | Configure secrets in Railway/Vercel env | CRITICAL | 1h |
| 13.7 | Add security headers (CSP, X-Frame-Options) | MEDIUM | 1h |
| 13.8 | Add health check with version info | LOW | 30m |

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
    "https://projects.benjaminblack.consulting",  # Production
    "http://localhost:3000",                       # Development
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

**Status:** Complete (December 9, 2025)

**Prerequisite:** Sprint 13 (Portfolio Security) recommended but not blocking.

### Tasks

| ID | Task | Priority | Est. |
|----|------|----------|------|
| **Backend (Railway)** | | | |
| 14.1 | Create Railway project | P0 | 30m |
| 14.2 | Configure Procfile/railway.toml | P0 | 1h |
| 14.3 | Set up environment variables | P0 | 1h |
| 14.4 | Configure PostgreSQL (Railway addon) | P0 | 2h |
| 14.5 | Set up Qdrant Cloud (free tier) | P1 | 1h |
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
DATABASE_URL=postgresql://...  # Railway PostgreSQL addon
QDRANT_URL=https://xxx-xxx.aws.cloud.qdrant.io  # Qdrant Cloud (free tier)
QDRANT_API_KEY=your_qdrant_cloud_api_key
ENVIRONMENT=production
ALLOWED_ORIGINS=https://projects.benjaminblack.consulting
```

**Vercel (Frontend):**
```
NEXT_PUBLIC_API_URL=https://etps-production.up.railway.app
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

| Service | Est. Cost | Notes |
|---------|-----------|-------|
| Railway (Hobby) | $5 | Includes $5 usage credit |
| Vercel | Free | Hobby tier |
| Qdrant Cloud | Free | 1GB free tier |
| Anthropic API | ~$10-20 | Usage-based |
| OpenAI API | ~$5 | Usage-based |
| **Total** | **~$20-30/month** | Mostly API usage |

---

## Phase 2 Sprints: Company Intelligence & Networking (PRD Section 5)

### Sprint 15: Hiring Manager Inference (PRD 5.3)

**Goal:** Use JD and company data to infer likely hiring managers.

**Tasks:**
- Extract reporting hints from JD (team keywords, title patterns)
- Use company size and industry norms for HM seniority heuristics
- Score and rank hiring manager candidates with confidence levels
- Output ranked list with justifications

### Sprint 16: Warm Contact Identification (PRD 5.4)

**Goal:** Identify potential warm contacts for networking.

**Tasks:**
- Find contacts based on shared schools (MIT, Tufts, Sloan)
- Find contacts based on shared employers (Fidelity, Santander)
- Find contacts based on shared industries (FS, consulting, defense)
- Generate relationship strength, relevance, and role compatibility scores

### Sprint 17: Networking Output Generation (PRD 5.5-5.6)

**Goal:** Generate networking outputs and outreach messages.

**Tasks:**
- Produce ranked lists of hiring managers and contacts
- Generate narrative summaries of org structure
- Create outreach messages (LinkedIn notes, InMail, email variants)
- Tailor messages by recipient type (HM, recruiter, peer, alumni)

---

## Phase 3 Sprints: Application Tracking & Workflows (PRD 5.8)

### Sprint 18: Application Status Tracking

**Goal:** Track application lifecycle and history.

**Tasks:**
- Track company, job, application status, contacts reached
- Store timeline and outcomes
- Link resume/cover letter versions used

### Sprint 19: Contact Management & Tasks

**Goal:** Manage networking contacts and follow-up tasks.

**Tasks:**
- Track tasks and reminders per contact
- Follow-up workflow automation

### Sprint 20+: Full Production Hardening

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
Phase 1C: Sprint 13 (Security) -> Sprint 14 (Deployment)
Phase 2:  Sprint 15 (HM Inference) -> Sprint 16 (Warm Contacts) -> Sprint 17 (Outreach)
Phase 3:  Sprint 18 (Tracking) -> Sprint 19 (Contact Mgmt) -> Sprint 20+ (Full Auth)
```

---

## Success Metrics

### Phase 1A-1B (Complete)
- Resume generation < 60 seconds
- ATS score > 75 for all outputs
- Zero banned phrases in outputs
- Skill-gap analysis accurate and actionable
- Company profile enrichment from JD

### Phase 1C (Target - Deployment)
- Deployed and accessible via public URL
- All generation flows work end-to-end
- Security scan passes
- Rate limiting active
- CORS restricted to production domain

### Phase 2 (Networking - Future)
- Hiring manager inference with confidence scores
- Warm contact identification with relationship strength
- Outreach message generation by recipient type

### Phase 3 (Tracking - Future)
- Application status tracking
- Contact management with follow-up tasks

---

*Last Updated: December 2025*
*For completed sprint details: `docs/archive/COMPLETED_SPRINTS.md`*

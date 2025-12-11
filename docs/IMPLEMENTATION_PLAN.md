# ETPS Implementation Plan
**Sprint Roadmap & Current Status**
**Version 2.1 - December 2025**

---

## Current Status

**Completed:** Phase 1A + Phase 1B + Phase 1C + Phase 1D (Sprints 1-18) - FULL PHASE 1 COMPLETE!

**Live URLs:**
- Frontend: https://etps.benjaminblack.consulting
- Backend: https://etps-production.up.railway.app

**Next Up:** Phase 2 - Company Intelligence & Networking (Sprints 19-21)

**Tests:** 783 passing

> For detailed task lists and implementation notes from completed sprints, see `docs/archive/COMPLETED_SPRINTS.md`

---

## Progress Summary

| Sprint | Phase | Status | Notes |
|--------|-------|--------|-------|
| Sprints 1-10 | Phase 1A | Done | Core Quality, Schema, LLM, Vector Search, Frontend MVP |
| Sprints 11-12 | Phase 1B | Done | Company Profile Enrichment |
| Sprint 13: Portfolio Security | Phase 1C | Done | Rate limiting, CORS, SSRF prevention, security headers |
| Sprint 14: Cloud Deployment | Phase 1C | Done | Railway + Vercel deployment |
| Sprint 15: Design System | Phase 1D | Done | Enterprise theme, design tokens, CircularProgress |
| Sprint 16: Hero & Visual Hierarchy | Phase 1D | Done | Hero state, ATS dashboard, page layout |
| Sprint 17: Info Architecture | Phase 1D | Done | Collapsibles, skill grouping, ResultsPreview |
| Sprint 18: Polish & Animations | Phase 1D | Done | Toast notifications, skeletons, animations, a11y |
| Sprints 19-21: Company Intelligence | Phase 2 | Not Started | Hiring Manager Inference, Warm Contacts, Outreach |
| Sprints 22+: Application Tracking | Phase 3 | Deferred | Tracking, Reminders, Full Auth |

---

## Phase Overview (Aligned with PRD Section 7.2)

```
Phase 1: Core (Sprints 1-18)                            COMPLETE
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

  Phase 1D: UI/UX Enhancement (Sprints 15-18)           COMPLETE
    - Design System & Enterprise Theme (Sprint 15)      COMPLETE
    - Hero Section & Visual Hierarchy (Sprint 16)       COMPLETE
    - Information Architecture & Data Viz (Sprint 17)   COMPLETE
    - Polish, Animations & Final Touches (Sprint 18)    COMPLETE
    - See: docs/UI_UX_IMPROVEMENT_PLAN.md

Phase 2: Company Intelligence & Networking (Sprints 19-21)  NOT STARTED
  - Hiring Manager Inference (PRD 5.3)
  - Warm Contact Identification (PRD 5.4)
  - Networking Suggestions & Outreach Drafts (PRD 5.5-5.6)

Phase 3: Application Tracking & Workflows (Sprints 22+)     DEFERRED
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

### Implementation Notes

**Database Configuration (db/database.py):**
- Added `DATABASE_URL` environment variable support (defaults to SQLite for dev)
- Handles Railway's `postgres://` → `postgresql://` URL conversion for SQLAlchemy 2.0
- Added startup event in `main.py` to auto-initialize database tables

**PostgreSQL Compatibility (db/models.py):**
- Removed B-tree index on `tags` JSON column (PostgreSQL can't B-tree index JSON)
- Note: Use GIN index for JSON indexing in PostgreSQL if needed in future

**Dependencies (requirements.txt):**
- Added `psycopg2-binary>=2.9.0` for PostgreSQL driver support

**Rate Limiter Fix (routers/*.py):**
- Fixed slowapi compatibility - parameter must be named exactly `request`
- Renamed `http_request: Request` → `request: Request`
- Renamed `request: BodySchema` → `body: BodySchema`
- Affected files: `resume.py`, `cover_letter.py`

**Data Migration:**
- Migrated from local SQLite: 8 experiences, 8 engagements, 28 bullets
- User candidate_profile JSON configured via direct DB update

### Acceptance Criteria

- [x] Backend accessible at Railway URL
- [x] Frontend accessible at Vercel URL
- [x] All API endpoints functional in production
- [x] Resume/cover letter generation works end-to-end
- [x] DOCX downloads work correctly
- [x] No CORS errors in browser console
- [x] Site loads in <3 seconds

**Estimated Effort:** 16.5 hours (actual: ~12 hours)

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

## Phase 1D: UI/UX Portfolio Enhancement (Sprints 15-18)

**Goal:** Transform ETPS from a functional application into a visually impressive portfolio piece with modern enterprise aesthetics.

**Design Philosophy:** Modern Enterprise - sophisticated blue-grays with teal accents, professional without being stuffy.

**Detailed Plan:** See `docs/UI_UX_IMPROVEMENT_PLAN.md`

### Sprint 15: Foundation & Design System

**Goal:** Establish design foundation and core visual improvements

**Status:** COMPLETE (December 2025)

**Completed Tasks:**
- Created design tokens (enterprise color palette with teal accents)
- Updated global styles and Tailwind config
- Enhanced header with logo and branding
- Created reusable components (CircularProgress, ProgressBar)
- Added Inter font from Google Fonts
- Implemented enterprise theme with semantic colors (success/warning/danger)

**Key Files Created/Modified:**
- `frontend/src/styles/design-tokens.css`
- `frontend/src/components/ui/circular-progress.tsx`
- `frontend/src/components/ui/progress-bar.tsx`
- `frontend/tailwind.config.ts`
- `frontend/src/app/globals.css`

**Estimated Effort:** 26.5 hours

### Sprint 16: Hero Section & Visual Hierarchy

**Goal:** Create engaging landing experience and improve information hierarchy

**Status:** COMPLETE (December 2025)

**Completed Tasks:**
- Created hero/landing state with value proposition
- Redesigned Job Details card with better spacing
- Implemented ATS Score dashboard with CircularProgress
- Improved page layout and spacing with gradient backgrounds
- Added subtle background patterns and teal accent borders
- Enhanced company profile display

**Key Files Created/Modified:**
- `frontend/src/app/page.tsx`
- `frontend/src/components/job-intake/JobIntakeForm.tsx`
- `frontend/src/components/job-intake/JobDetailsCard.tsx`
- `frontend/src/components/analysis/AnalysisResults.tsx`

**Estimated Effort:** 37 hours

### Sprint 17: Information Architecture & Data Visualization

**Goal:** Reduce information density and improve data presentation

**Status:** COMPLETE (December 2025)

**Completed Tasks:**
- Refactored Capability Cluster Panel with Collapsible sections
- Grouped skills by match type (Matched/Partial/Missing) with SkillGroup component
- Redesigned Context Notes with collapsible UI, tooltips, and quick-insert buttons
- Added CircularProgress and ProgressBar components for visual scores
- Created ResultsPreview card with metrics summary
- Added Expand All/Collapse All toggles throughout
- Enhanced Results Panel with collapsible roles and improved styling

**Key Files Created/Modified:**
- `frontend/src/components/skills/SkillGroup.tsx` (new)
- `frontend/src/components/skills/SkillSelectionPanel.tsx`
- `frontend/src/components/results/ResultsPreview.tsx` (new)
- `frontend/src/components/results/index.ts` (new)
- `frontend/src/components/generation/ResultsPanel.tsx`
- `frontend/src/components/job-intake/ContextNotesField.tsx`
- `frontend/src/components/capability/CapabilityClusterPanel.tsx`
- `frontend/src/components/ui/collapsible.tsx` (shadcn)
- `frontend/src/components/ui/tooltip.tsx` (shadcn)

**Estimated Effort:** 44 hours

### Sprint 18: Polish, Animations & Final Touches

**Goal:** Add micro-interactions, loading states, and final polish

**Status:** Not Started

**Tasks:**
- Add smooth transitions to all interactive elements
- Implement skeleton loaders and loading states
- Create toast notification system
- Design helpful empty states
- Accessibility and performance audits
- Update documentation and screenshots

**Estimated Effort:** 61 hours

**Total Phase 1D Effort:** 168.5 hours (~4 weeks)

---

## Phase 2 Sprints: Company Intelligence & Networking (PRD Section 5)

### Sprint 19: Hiring Manager Inference (PRD 5.3)

**Goal:** Use JD and company data to infer likely hiring managers.

**Tasks:**
- Extract reporting hints from JD (team keywords, title patterns)
- Use company size and industry norms for HM seniority heuristics
- Score and rank hiring manager candidates with confidence levels
- Output ranked list with justifications

### Sprint 20: Warm Contact Identification (PRD 5.4)

**Goal:** Identify potential warm contacts for networking.

**Tasks:**
- Find contacts based on shared schools (MIT, Tufts, Sloan)
- Find contacts based on shared employers (Fidelity, Santander)
- Find contacts based on shared industries (FS, consulting, defense)
- Generate relationship strength, relevance, and role compatibility scores

### Sprint 21: Networking Output Generation (PRD 5.5-5.6)

**Goal:** Generate networking outputs and outreach messages.

**Tasks:**
- Produce ranked lists of hiring managers and contacts
- Generate narrative summaries of org structure
- Create outreach messages (LinkedIn notes, InMail, email variants)
- Tailor messages by recipient type (HM, recruiter, peer, alumni)

---

## Phase 3 Sprints: Application Tracking & Workflows (PRD 5.8)

### Sprint 22: Application Status Tracking

**Goal:** Track application lifecycle and history.

**Tasks:**
- Track company, job, application status, contacts reached
- Store timeline and outcomes
- Link resume/cover letter versions used

### Sprint 23: Contact Management & Tasks

**Goal:** Manage networking contacts and follow-up tasks.

**Tasks:**
- Track tasks and reminders per contact
- Follow-up workflow automation

### Sprint 24+: Full Production Hardening

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

- **Total Tests:** 783 passing
- **Coverage:** All Sprint 1-18 functionality tested
- **Key Test Files:** test_bullet_rewriter.py, test_truthfulness_check.py, test_summary_rewrite.py, test_text_output.py, test_vector_store.py, test_approved_outputs.py, test_pagination_allocation.py, test_job_parser_extraction.py, test_skill_selection.py, test_capability_clusters.py, test_company_enrichment.py, test_security.py, test_skills_formatter.py

---

## Dependencies

### External
- Anthropic API Key (Claude LLM)
- OpenAI API Key (embeddings)
- Qdrant (vector store)

### Sprint Dependencies
```
Phase 1C: Sprint 13 (Security) -> Sprint 14 (Deployment)
Phase 1D: Sprint 15 (Design Foundation) -> Sprint 16 (Hero) -> Sprint 17 (Info Arch) -> Sprint 18 (Polish)
Phase 2:  Sprint 19 (HM Inference) -> Sprint 20 (Warm Contacts) -> Sprint 21 (Outreach)
Phase 3:  Sprint 22 (Tracking) -> Sprint 23 (Contact Mgmt) -> Sprint 24+ (Full Auth)
```

---

## Success Metrics

### Phase 1A-1B (Complete)
- Resume generation < 60 seconds
- ATS score > 75 for all outputs
- Zero banned phrases in outputs
- Skill-gap analysis accurate and actionable
- Company profile enrichment from JD

### Phase 1C (Complete - Deployment)
- [x] Deployed and accessible via public URL (https://etps.benjaminblack.consulting)
- [x] All generation flows work end-to-end
- [x] Security scan passes
- [x] Rate limiting active (slowapi)
- [x] CORS restricted to production domain
- [x] PostgreSQL database (Railway)
- [x] Auto-deploy on git push

### Phase 2 (Networking - Future)
- Hiring manager inference with confidence scores
- Warm contact identification with relationship strength
- Outreach message generation by recipient type

### Phase 3 (Tracking - Future)
- Application status tracking
- Contact management with follow-up tasks

---

*Last Updated: December 11, 2025*
*For completed sprint details: `docs/archive/COMPLETED_SPRINTS.md`*

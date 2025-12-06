# ETPS Implementation Plan
**Full PRD Implementation Roadmap**
**Version 1.2 — December 2025**
*Merged content from IMPLEMENTATION_ROADMAP.md (v1.3.0 Schema)*

---

## Executive Summary

This document provides a detailed implementation plan to build ETPS to full PRD specification. The plan is organized into sprints with specific tasks, acceptance criteria, and dependencies.

**Current State:** Phase 1A complete with Resume Critic, Skill-Gap Analysis, and Cover Letter Critic implemented.

**Target State:** Full Phase 1 (Core Quality), Phase 2 (Company Intelligence), and Phase 3 (Application Tracking) as defined in ETPS_PRD.md.

---

## Progress Summary

| Sprint | Status | Completion Date | Notes |
|--------|--------|-----------------|-------|
| Sprint 1: Resume Critic Agent | ✅ COMPLETE | Dec 2025 | Full critic loop with iteration, ATS scoring, style enforcement |
| Sprint 2: Skill-Gap Analysis | ✅ COMPLETE | Dec 2025 | Semantic matching with OpenAI embeddings, positioning strategies |
| Sprint 3: Cover Letter Critic | ✅ COMPLETE | Dec 2025 | Critic iteration loop, banned phrase detection, LLM revision |
| Sprint 4: Schema & Data Migration | 🔲 NOT STARTED | - | v1.3.0 schema, engagement structure |
| Sprint 5: Bullet Rewriting | 🔲 NOT STARTED | - | LLM-powered rewriting with STAR notes |
| Sprint 6: Version History & Plain Text | 🔲 NOT STARTED | - | |
| Sprint 7: Qdrant Integration | 🔲 NOT STARTED | - | Vector search setup |
| Sprint 8: Learning from Approved Outputs | 🔲 NOT STARTED | - | |
| Sprint 9-10: Frontend MVP | 🔲 NOT STARTED | - | Next.js + Job Intake UI |
| Sprint 11-14: Company Intelligence | 🔲 NOT STARTED | - | Phase 2 |
| Sprint 15-17: Application Tracking | 🔲 NOT STARTED | - | Phase 3 |
| Sprint 18: Production Hardening | 🔲 NOT STARTED | - | ⚠️ Security & reliability (8 P0 tasks) |
| Sprint 19: Deployment | 🔲 NOT STARTED | - | Railway + Vercel |

### Test Coverage
- **Total Tests:** 53 passing
- **Test Files:** test_resume_critic.py, test_skill_gap.py, test_cover_letter_critic.py, + others
- **Coverage:** All Sprint 1-3 functionality tested

---

## Implementation Phases Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1A: Core Quality (Sprints 1-3) ✅ COMPLETE               │
│ - Resume Critic Agent                    ✅                     │
│ - ATS Scoring                            ✅                     │
│ - Style Enforcement                      ✅                     │
│ - Skill-Gap Analysis                     ✅                     │
│ - Cover Letter Critic                    ✅                     │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1B: Schema Migration (Sprint 4)                          │
│ - v1.3.0 Schema (engagement hierarchy)                          │
│ - Resume Data Update                                            │
│ - DOCX Generator Updates                                        │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1C: LLM Enhancement (Sprints 5-6)                        │
│ - Bullet Rewriting                                              │
│ - Version History                                               │
│ - Text/Plain Output                                             │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1D: Vector Search & Learning (Sprints 7-8)               │
│ - Qdrant Integration                                            │
│ - Semantic Bullet Matching                                      │
│ - Learning from Approved Outputs                                │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1E: Frontend MVP (Sprints 9-10)                          │
│ - Next.js Setup                                                 │
│ - Job Intake Page                                               │
│ - Generate & Download Workflow                                  │
│ - Skill-Gap Display                                             │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 2: Company Intelligence (Sprints 11-14)                  │
│ - Company Profile Enrichment                                    │
│ - Hiring Manager Inference                                      │
│ - Warm Contact Identification                                   │
│ - Networking Output Generation                                  │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 3: Application Tracking (Sprints 15-17)                  │
│ - Application Status Tracking                                   │
│ - Contact Management                                            │
│ - Reminders & Tasks                                             │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 4: Production Readiness (Sprint 18)                      │
│ - Security Hardening                                            │
│ - Authentication & Authorization                                │
│ - Rate Limiting & Input Validation                              │
│ - Error Handling & Logging                                      │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 5: Deployment (Sprint 19)                                │
│ - Railway Backend Deployment                                    │
│ - Vercel Frontend Deployment                                    │
│ - Production Configuration                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1A: Core Quality

### Sprint 1: Resume Critic Agent (PRD 4.1-4.5) ✅ COMPLETE

**Goal:** Implement a critic agent that evaluates resume quality against a rubric and triggers revisions.

**Status:** ✅ Completed December 2025

#### Tasks

| ID | Task | File(s) | PRD Ref | Status |
|----|------|---------|---------|--------|
| 1.1.1 | Define ResumeCriticResult schema | `schemas/critic.py` | 4.3 | ✅ |
| 1.1.2 | Implement resume rubric evaluation | `services/critic.py` | 4.3 | ✅ |
| 1.1.3 | Add JD alignment scoring | `services/critic.py` | 4.3 | ✅ |
| 1.1.4 | Add clarity/conciseness scoring | `services/critic.py` | 4.3 | ✅ |
| 1.1.5 | Add impact orientation scoring | `services/critic.py` | 4.3 | ✅ |
| 1.1.6 | Add tone validation | `services/critic.py` | 4.3 | ✅ |
| 1.1.7 | Add formatting fidelity check | `services/critic.py` | 4.3 | ✅ |
| 1.1.8 | Add hallucination detection | `services/critic.py` | 4.3 | ✅ |
| 1.1.9 | Implement critic iteration loop | `services/resume_tailor.py` | 4.4 | ✅ |
| 1.1.10 | Add max iterations config | `config/config.yaml` | 4.4 | ✅ |
| 1.1.11 | Add critic logging | `services/critic.py` | 4.6 | ✅ |
| 1.1.12 | Write unit tests | `test_resume_critic.py` | - | ✅ |

#### Acceptance Criteria
- [x] Critic evaluates resume against all rubric categories
- [x] Critic returns structured scores (0-100) for each category
- [x] Critic identifies specific issues with actionable feedback
- [x] Iteration loop retries up to 3 times on failure
- [x] All critic decisions logged to database

#### Implementation Notes
- Implemented in `services/critic.py` (~2600 lines)
- Comprehensive rubric with 6 scoring dimensions
- MockLLM for tone inference with real LLM integration ready
- 15 unit tests passing

#### Schema: ResumeCriticResult
```python
class ResumeCriticResult(BaseModel):
    passed: bool
    overall_score: float  # 0-100
    scores: dict  # {alignment: 85, clarity: 90, impact: 75, tone: 88, ...}
    issues: List[CriticIssue]  # [{category, severity, message, suggestion}]
    ats_score: float  # 0-100
    iteration: int
    should_retry: bool
```

---

### Sprint 2: Skill-Gap Analysis with Semantic Matching (PRD 1.4, 2.7) ✅ COMPLETE

**Goal:** Implement comprehensive skill-gap analysis with semantic embedding matching.

**Status:** ✅ Completed December 2025

**Note:** ATS scoring and style enforcement were integrated into Sprint 1 (Resume Critic). This sprint focused on semantic skill matching.

#### Tasks

| ID | Task | File(s) | PRD Ref | Status |
|----|------|---------|---------|--------|
| 2.1 | Define SkillGapResponse schema | `schemas/skill_gap.py` | 2.7 | ✅ |
| 2.2 | Implement embeddings service | `services/embeddings.py` | 6.3 | ✅ |
| 2.3 | OpenAI embedding integration | `services/embeddings.py` | 6.4 | ✅ |
| 2.4 | Semantic skill matching | `services/skill_gap.py` | 2.7 | ✅ |
| 2.5 | Weak signal detection | `services/skill_gap.py` | 2.7 | ✅ |
| 2.6 | LLM-based gap categorization | `services/skill_gap.py` | 2.7 | ✅ |
| 2.7 | Positioning strategy generation | `services/skill_gap.py` | 2.7 | ✅ |
| 2.8 | Database caching with 24h expiry | `services/skill_gap.py` | - | ✅ |
| 2.9 | Thread-safe singleton patterns | `services/skill_gap.py` | - | ✅ |
| 2.10 | Write unit tests | `test_skill_gap.py` | - | ✅ |

#### Acceptance Criteria
- [x] All JD skills extracted and categorized
- [x] User skills matched with semantic similarity (OpenAI embeddings)
- [x] Gaps identified with importance levels (critical/important/nice-to-have)
- [x] Weak signals detected for adjacent skills
- [x] Positioning strategies suggested for each gap
- [x] Results cached in database for 24 hours

#### Implementation Notes
- `services/embeddings.py` - BaseEmbeddingService, MockEmbeddingService, OpenAIEmbeddingService
- `services/skill_gap.py` - ~1300 lines with full semantic matching
- Similarity threshold tuned to 0.60 for OpenAI text-embedding-3-small
- 24 unit tests passing

#### Schema: SkillGapResponse
```python
class SkillGapResponse(BaseModel):
    job_profile_id: int
    user_id: int
    skill_match_score: float  # 0-100
    recommendation: str  # strong_match, moderate_match, weak_match
    matched_skills: List[MatchedSkill]
    skill_gaps: List[SkillGap]  # with importance and positioning_strategy
    weak_signals: List[WeakSignal]  # adjacent/related skills
    positioning_summary: str
    analysis_timestamp: str
```

---

### Sprint 3: Cover Letter Critic (PRD 3.7, 4.8) ✅ COMPLETE

**Goal:** Implement cover letter critic with iteration loop and LLM-based revision.

**Status:** ✅ Completed December 2025

**Note:** Originally planned as Sprint 5, moved up to Sprint 3 to complete Phase 1A Core Quality.

#### Tasks

| ID | Task | File(s) | PRD Ref | Status |
|----|------|---------|---------|--------|
| 3.1 | Define CriticIssue schema | `schemas/cover_letter.py` | 4.3 | ✅ |
| 3.2 | Define CoverLetterCriticResult schema | `schemas/cover_letter.py` | 4.3 | ✅ |
| 3.3 | Add iteration tracking to GeneratedCoverLetter | `schemas/cover_letter.py` | 4.3 | ✅ |
| 3.4 | Implement evaluate_cover_letter() | `services/cover_letter.py` | 4.3 | ✅ |
| 3.5 | Implement critic iteration loop | `services/cover_letter.py` | 3.7 | ✅ |
| 3.6 | Add revise_cover_letter() to LLM interface | `services/llm/base.py` | 3.7 | ✅ |
| 3.7 | Implement MockLLM revision with phrase replacements | `services/llm/mock_llm.py` | 3.7 | ✅ |
| 3.8 | Add CriticLog model for persistence | `db/models.py` | 4.6 | ✅ |
| 3.9 | Write unit tests | `test_cover_letter_critic.py` | - | ✅ |

#### Acceptance Criteria
- [x] Cover letter evaluated against quality rubric
- [x] Banned phrases detected and flagged
- [x] Tone compliance assessed
- [x] ATS keyword coverage analyzed
- [x] Issues aggregated with severity levels
- [x] Iteration loop: generate → evaluate → revise (max 3 iterations)
- [x] LLM revision replaces banned phrases with alternatives

#### Implementation Notes
- Critic iteration loop in `services/cover_letter.py` (lines 1114-1340)
- Quality threshold: 75 points (configurable)
- Max iterations: 3 (configurable)
- MockLLM includes 40+ banned phrase replacements
- 14 unit tests passing

---

## Phase 1B: Schema Migration

### Sprint 4: Schema & Data Migration (v1.3.0)

**Goal:** Migrate database schema to v1.3.0 with engagement hierarchy and update resume data.

**Source:** Merged from IMPLEMENTATION_ROADMAP.md

#### Tasks - Database Schema

| ID | Task | File(s) | Description | Priority |
|----|------|---------|-------------|----------|
| 4.1.1 | Add `engagements` table | `db/models.py` | New table: id, experience_id, client, project_name, project_type, date_range_label, domain_tags, tech_tags, order | P0 |
| 4.1.2 | Update `bullets` table | `db/models.py` | Add engagement_id FK (nullable for non-consulting roles) | P0 |
| 4.1.3 | Update `experiences` table | `db/models.py` | Add employer_type, role_summary, ai_systems_built, governance_frameworks_created, fs_domain_relevance, tools_and_technologies | P0 |
| 4.1.4 | Update `users` table | `db/models.py` | Add primary_identity, specializations, target_roles, ai_systems_builder, portfolio_url, linkedin_meta (JSON) | P0 |
| 4.1.5 | Update `skills` table | `db/models.py` | Add category, level, core fields | P0 |
| 4.1.6 | Add education fields | `db/models.py` | Add prestige_weight, executive_credibility_score, language_fluency | P1 |

#### Tasks - Pydantic Schemas

| ID | Task | File(s) | Description | Priority |
|----|------|---------|-------------|----------|
| 4.2.1 | Add Engagement schema | `schemas/resume_tailor.py` | New Engagement model with client, project_name, bullets | P0 |
| 4.2.2 | Update SelectedRole schema | `schemas/resume_tailor.py` | Include engagements in role output | P0 |
| 4.2.3 | Update User schema | `schemas/user.py` | Add candidate profile fields | P0 |
| 4.2.4 | Update Skill schema | `schemas/skill.py` | Add category, level, core | P0 |
| 4.2.5 | Update Education schema | `schemas/education.py` | Add prestige/credibility fields | P1 |

#### Tasks - Resume Data Update

| ID | Task | File(s) | Description | Priority |
|----|------|---------|-------------|----------|
| 4.3.1 | Update user profile | `migrations/` | Update email, phone, portfolio_url, primary_identity, specializations | P0 |
| 4.3.2 | Add BBC (10/2025) experience | `migrations/` | Independent AI Strategist & Builder | P0 |
| 4.3.3 | Add BBC (8/2022-9/2024) experience | `migrations/` | Principal Consultant (Edward Jones, Darling) | P0 |
| 4.3.4 | Create engagement records | `migrations/` | Edward Jones, Darling, Squark, Vestmark, John Hancock, Olmstead, Fidelity | P0 |
| 4.3.5 | Update skills with categories | `migrations/` | AI/ML, Governance, Cloud, Tech categories | P0 |

#### Tasks - DOCX Generator Updates

| ID | Task | File(s) | Description | Priority |
|----|------|---------|-------------|----------|
| 4.4.1 | Update section order | `services/docx_resume.py` | Summary → Experience → Skills → Education | P0 |
| 4.4.2 | Add engagement formatting | `services/docx_resume.py` | Render engagements under consulting roles | P0 |
| 4.4.3 | Update skills section format | `services/docx_resume.py` | Category-grouped format (AI/ML: ..., Cloud: ...) | P0 |

#### Tasks - Resume Tailor Updates

| ID | Task | File(s) | Description | Priority |
|----|------|---------|-------------|----------|
| 4.5.1 | Engagement-aware selection | `services/resume_tailor.py` | Select engagements based on JD relevance | P0 |
| 4.5.2 | Bullet ordering within engagement | `services/resume_tailor.py` | Order bullets by relevance score | P0 |
| 4.5.3 | Write migration script | `migrations/v1_3_0_schema_migration.py` | Backup data, create tables, migrate bullets | P0 |
| 4.5.4 | Write unit tests | `tests/test_schema_migration.py` | Test migration and rollback | P1 |

#### Acceptance Criteria
- [ ] All December 2025 resume content in database
- [ ] Engagements properly structured for BBC roles
- [ ] DOCX output matches new resume format (Skills before Education)
- [ ] Skills section uses category grouping
- [ ] Migration script handles rollback
- [ ] All existing tests still pass after migration

#### Engagement Structure Example
```
Benjamin Black Consulting | Boston, MA                    10/2025 – Present
Independent AI Strategist & Builder
  [Role summary bullet]

  Edward Jones — Enterprise Data Strategy & Governance
    • Bullet 1
    • Bullet 2

  Darling Consulting Group — Data Strategy & Analytics Portal
    • Bullet 1
```

---

## Phase 1C: LLM Enhancement

### Sprint 5: Bullet Rewriting (PRD 2.4, 2.6)

**Goal:** Implement LLM-powered bullet rewriting to optimize for JD keywords while preserving truth.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.4.1 | Create bullet rewriting prompt template | `services/llm/prompts/` | 2.4 | P0 |
| 1.4.2 | Implement bullet rewriter service | `services/bullet_rewriter.py` | 2.4 | P0 |
| 1.4.3 | Add STAR notes integration | `services/bullet_rewriter.py` | 2.6 | P1 |
| 1.4.4 | Implement version history storage | `db/models.py` | 2.6 | P0 |
| 1.4.5 | Add rewrite validation (no hallucination) | `services/bullet_rewriter.py` | 4.3 | P0 |
| 1.4.6 | Track original vs rewritten text | `schemas/resume_tailor.py` | 2.6 | P0 |
| 1.4.7 | Add rewrite toggle (enable/disable) | `schemas/resume_tailor.py` | 2.4 | P1 |
| 1.4.8 | Integrate with resume tailor flow | `services/resume_tailor.py` | 2.4 | P0 |
| 1.4.9 | Write unit tests | `tests/test_bullet_rewriter.py` | - | P1 |

#### Acceptance Criteria
- [ ] Bullets rewritten to include JD keywords
- [ ] Original text preserved in version history
- [ ] No factual changes (dates, metrics, employers)
- [ ] STAR notes used to enrich rewrites when available
- [ ] Rewriting can be enabled/disabled per request

#### Prompt Strategy
```
System: You are a resume bullet optimizer. Rewrite bullets to:
1. Include relevant keywords from the job description
2. Strengthen action verbs
3. Maintain all factual accuracy (never change metrics, dates, or employers)
4. Keep similar length (max 2 lines)

Original: {bullet_text}
STAR Notes: {star_notes}
Target Keywords: {jd_keywords}

Output: Rewritten bullet only, no explanation.
```

---

### Sprint 6: Version History & Plain Text (PRD 2.5, 2.6)

**Goal:** Implement bullet version history and text/plain output format.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.6.1 | Design version history JSON schema | `db/models.py` | 2.6 | P0 |
| 1.6.2 | Implement version tracking on save | `services/bullet_rewriter.py` | 2.6 | P0 |
| 1.6.3 | Add version history retrieval API | `routers/resume.py` | 2.6 | P1 |
| 1.6.4 | Implement plain text resume generator | `services/text_resume.py` | 2.5 | P0 |
| 1.6.5 | Implement plain text cover letter generator | `services/text_cover_letter.py` | 2.5 | P0 |
| 1.6.6 | Add output format selection to API | `routers/resume.py` | 2.5 | P0 |
| 1.6.7 | Write unit tests | `tests/test_text_output.py` | - | P1 |

#### Acceptance Criteria
- [ ] All bullet rewrites stored in version history
- [ ] Version history includes timestamp, context, original ref
- [ ] Plain text output ATS-friendly (no special characters)
- [ ] API supports format param: docx, text, json

---

## Phase 1D: Vector Search & Learning

### Sprint 7: Qdrant Integration (PRD 6.3)

**Goal:** Set up Qdrant vector store for semantic search.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.7.1 | Add Qdrant to requirements | `requirements.txt` | 6.3 | P0 |
| 1.7.2 | Create Qdrant client wrapper | `services/vector_store.py` | 6.3 | P0 |
| 1.7.3 | Define collection schemas | `services/vector_store.py` | 6.3 | P0 |
| 1.7.4 | Implement bullet embedding generation | `services/embeddings.py` | 6.3 | P0 |
| 1.7.5 | Implement job profile embedding | `services/embeddings.py` | 6.3 | P0 |
| 1.7.6 | Create bullet indexing service | `services/vector_store.py` | 6.3 | P0 |
| 1.7.7 | Create job similarity search | `services/vector_store.py` | 6.3 | P1 |
| 1.7.8 | Add embedding model config | `config/config.yaml` | 6.4 | P1 |
| 1.7.9 | Write integration tests | `tests/test_vector_store.py` | - | P1 |

#### Acceptance Criteria
- [ ] Qdrant running locally with persistent storage
- [ ] All bullets indexed with embeddings
- [ ] Job profiles indexed for similarity search
- [ ] Semantic search returns relevant bullets

#### Collections
```
etps_bullets: {id, text, embedding, tags, experience_id, usage_count}
etps_jobs: {id, title, embedding, company, requirements}
etps_approved_outputs: {id, type, embedding, job_context, content}
```

---

### Sprint 8: Learning from Approved Outputs (PRD 4.7)

**Goal:** Store approved outputs and retrieve similar examples for new requests.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.8.1 | Create ApprovedOutput model | `db/models.py` | 4.7 | P0 |
| 1.8.2 | Implement output approval API | `routers/outputs.py` | 4.7 | P0 |
| 1.8.3 | Index approved outputs in Qdrant | `services/vector_store.py` | 4.7 | P0 |
| 1.8.4 | Implement similar output retrieval | `services/output_retrieval.py` | 4.7 | P0 |
| 1.8.5 | Integrate examples into generation prompts | `services/resume_tailor.py` | 4.7 | P1 |
| 1.8.6 | Add quality comparison in critic | `services/resume_critic.py` | 4.7 | P2 |
| 1.8.7 | Write unit tests | `tests/test_approved_outputs.py` | - | P1 |

#### Acceptance Criteria
- [ ] Users can approve generated outputs
- [ ] Approved outputs indexed with metadata
- [ ] Similar examples retrieved for new jobs
- [ ] Examples guide generation without copy-paste

---

## Phase 1E: Frontend MVP

### Sprint 9: Next.js Setup (PRD 6.6)

**Goal:** Set up Next.js frontend with Tailwind and shadcn/ui.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.9.1 | Initialize Next.js with TypeScript | `frontend/` | 6.6 | P0 |
| 1.9.2 | Configure Tailwind CSS | `frontend/tailwind.config.ts` | 6.6 | P0 |
| 1.9.3 | Install and configure shadcn/ui | `frontend/components/ui/` | 6.6 | P0 |
| 1.9.4 | Create base layout component | `frontend/src/app/layout.tsx` | 6.6 | P0 |
| 1.9.5 | Set up API client (fetch wrapper) | `frontend/src/lib/api.ts` | 6.6 | P0 |
| 1.9.6 | Configure environment variables | `frontend/.env.local` | 6.9 | P1 |
| 1.9.7 | Create shared types from backend schemas | `frontend/src/types/` | - | P1 |

#### Acceptance Criteria
- [ ] Next.js app runs locally
- [ ] Tailwind styling works
- [ ] shadcn/ui components available
- [ ] API client connects to backend

---

### Sprint 10: Job Intake & Generation UI (PRD 6.6)

**Goal:** Build the main job intake page with generation workflow.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.10.1 | Create job intake form component | `frontend/src/components/JobIntakeForm.tsx` | 6.6 | P0 |
| 1.10.2 | Add JD text area with URL fetch option | `frontend/src/components/JobIntakeForm.tsx` | 6.6 | P0 |
| 1.10.3 | Add context notes field | `frontend/src/components/JobIntakeForm.tsx` | 6.6 | P1 |
| 1.10.4 | Create generation buttons (Resume, CL) | `frontend/src/components/GenerateButtons.tsx` | 6.6 | P0 |
| 1.10.5 | Add loading states and progress | `frontend/src/components/GenerateButtons.tsx` | 6.6 | P0 |
| 1.10.6 | Create download buttons (docx, txt, json) | `frontend/src/components/DownloadButtons.tsx` | 6.6 | P0 |
| 1.10.7 | Build results display panel | `frontend/src/components/ResultsPanel.tsx` | 6.6 | P0 |
| 1.10.8 | Add skill-gap analysis display | `frontend/src/components/SkillGapPanel.tsx` | 6.6 | P1 |
| 1.10.9 | Add ATS score display | `frontend/src/components/ATSScoreCard.tsx` | 6.6 | P1 |
| 1.10.10 | Wire up to backend APIs | `frontend/src/app/page.tsx` | 6.6 | P0 |

#### Acceptance Criteria
- [ ] User can paste JD text or URL
- [ ] Generate buttons trigger backend calls
- [ ] Download buttons work for all formats
- [ ] Skill-gap analysis displayed clearly
- [ ] ATS score shown with breakdown

---

## Phase 2: Company Intelligence

### Sprint 11: Company Profile Enrichment (PRD 5.1-5.2)

**Goal:** Enrich company profiles with web data and intelligence.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 2.1.1 | Create company enrichment service | `services/company_enrichment.py` | 5.1 | P0 |
| 2.1.2 | Extract company from JD | `services/company_enrichment.py` | 5.1 | P0 |
| 2.1.3 | Fetch company website data | `services/company_enrichment.py` | 5.1 | P1 |
| 2.1.4 | Extract industry, size, HQ | `services/company_enrichment.py` | 5.1 | P1 |
| 2.1.5 | Infer culture signals | `services/company_enrichment.py` | 5.1 | P2 |
| 2.1.6 | Infer data/AI maturity | `services/company_enrichment.py` | 5.1 | P2 |
| 2.1.7 | Store enriched profile | `db/models.py` | 5.1 | P0 |
| 2.1.8 | Add company profile API | `routers/company.py` | 5.1 | P1 |
| 2.1.9 | Write unit tests | `tests/test_company.py` | - | P1 |

---

### Sprint 12: Hiring Manager Inference (PRD 5.3)

**Goal:** Infer likely hiring managers from job and company data.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 2.2.1 | Create hiring manager inference service | `services/hiring_manager.py` | 5.3 | P0 |
| 2.2.2 | Extract reporting hints from JD | `services/hiring_manager.py` | 5.3 | P0 |
| 2.2.3 | Parse team keywords | `services/hiring_manager.py` | 5.3 | P0 |
| 2.2.4 | Score and rank candidates | `services/hiring_manager.py` | 5.3 | P0 |
| 2.2.5 | Add confidence levels | `services/hiring_manager.py` | 5.3 | P1 |
| 2.2.6 | Store inference results | `db/models.py` | 5.3 | P0 |
| 2.2.7 | Add API endpoint | `routers/networking.py` | 5.3 | P1 |
| 2.2.8 | Write unit tests | `tests/test_hiring_manager.py` | - | P1 |

---

### Sprint 13: Warm Contact Identification (PRD 5.4)

**Goal:** Identify warm contacts based on shared connections.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 2.3.1 | Create contact matching service | `services/contact_matcher.py` | 5.4 | P0 |
| 2.3.2 | Match shared schools | `services/contact_matcher.py` | 5.4 | P0 |
| 2.3.3 | Match shared employers | `services/contact_matcher.py` | 5.4 | P0 |
| 2.3.4 | Match shared industries | `services/contact_matcher.py` | 5.4 | P1 |
| 2.3.5 | Calculate relationship strength | `services/contact_matcher.py` | 5.4 | P0 |
| 2.3.6 | Calculate role compatibility | `services/contact_matcher.py` | 5.4 | P1 |
| 2.3.7 | Rank contacts by warmth | `services/contact_matcher.py` | 5.4 | P0 |
| 2.3.8 | Add contact API | `routers/networking.py` | 5.4 | P1 |
| 2.3.9 | Write unit tests | `tests/test_contacts.py` | - | P1 |

---

### Sprint 14: Networking Outputs (PRD 5.5-5.6)

**Goal:** Generate networking outputs and outreach messages.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 2.4.1 | Create networking plan generator | `services/networking.py` | 5.5 | P0 |
| 2.4.2 | Generate ranked contact lists | `services/networking.py` | 5.5 | P0 |
| 2.4.3 | Generate org structure narrative | `services/networking.py` | 5.5 | P1 |
| 2.4.4 | Create outreach message generator | `services/outreach.py` | 5.6 | P0 |
| 2.4.5 | Add LinkedIn connection note template | `services/outreach.py` | 5.6 | P0 |
| 2.4.6 | Add InMail template | `services/outreach.py` | 5.6 | P1 |
| 2.4.7 | Add email template | `services/outreach.py` | 5.6 | P1 |
| 2.4.8 | Tailor by recipient type | `services/outreach.py` | 5.6 | P0 |
| 2.4.9 | Generate DOCX networking report | `services/docx_networking.py` | 5.5 | P2 |
| 2.4.10 | Add networking UI panel | `frontend/src/components/NetworkingPanel.tsx` | 6.6 | P1 |

---

## Phase 3: Application Tracking

### Sprint 15: Application Status Tracking (PRD 5.8)

**Goal:** Track application status through the hiring pipeline.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 3.1.1 | Define application status enum | `db/models.py` | 5.8 | P0 |
| 3.1.2 | Create application update API | `routers/applications.py` | 5.8 | P0 |
| 3.1.3 | Add status history tracking | `db/models.py` | 5.8 | P1 |
| 3.1.4 | Create application list view | `frontend/src/app/applications/page.tsx` | 5.8 | P0 |
| 3.1.5 | Add application detail view | `frontend/src/app/applications/[id]/page.tsx` | 5.8 | P1 |
| 3.1.6 | Add status update UI | `frontend/src/components/StatusUpdate.tsx` | 5.8 | P0 |
| 3.1.7 | Write unit tests | `tests/test_applications.py` | - | P1 |

---

### Sprint 16: Contact Management & Tasks (PRD 5.8)

**Goal:** Manage contacts and create follow-up tasks.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 3.2.1 | Create contact management API | `routers/contacts.py` | 5.8 | P0 |
| 3.2.2 | Add contact notes and history | `db/models.py` | 5.8 | P1 |
| 3.2.3 | Create task/reminder model | `db/models.py` | 5.8 | P0 |
| 3.2.4 | Add task creation API | `routers/tasks.py` | 5.8 | P0 |
| 3.2.5 | Create task list UI | `frontend/src/components/TaskList.tsx` | 5.8 | P0 |
| 3.2.6 | Add task completion workflow | `frontend/src/components/TaskList.tsx` | 5.8 | P0 |
| 3.2.7 | Write unit tests | `tests/test_tasks.py` | - | P1 |

---

### Sprint 18: Production Hardening (Security & Reliability)

**Goal:** Address security vulnerabilities and production readiness requirements identified in security review.

**Priority:** Must complete before any public deployment.

#### Tasks - Critical (Blockers)

| ID | Task | File(s) | Severity | Priority |
|----|------|---------|----------|----------|
| 17.1 | Implement JWT authentication | `routers/*.py`, `middleware/` | HIGH | P0 |
| 17.2 | Add ownership validation to DB queries | `routers/*.py` | HIGH | P0 |
| 17.3 | Implement SSRF prevention on URL fetch | `utils/text_processing.py` | HIGH | P0 |
| 17.4 | Add rate limiting middleware | `main.py` | HIGH | P0 |
| 17.5 | Sanitize error messages (no info leakage) | `routers/*.py` | HIGH | P0 |
| 17.6 | Restrict CORS HTTP methods | `main.py` | CRITICAL | P0 |
| 17.7 | Add request body size limits | `main.py`, `schemas/*.py` | HIGH | P0 |
| 17.8 | Implement secrets management | `config/` | CRITICAL | P0 |

#### Tasks - Medium Priority

| ID | Task | File(s) | Severity | Priority |
|----|------|---------|----------|----------|
| 17.9 | Add security headers middleware | `main.py` | MEDIUM | P1 |
| 17.10 | Implement audit logging | `services/logging.py` | MEDIUM | P1 |
| 17.11 | Add CSRF protection | `middleware/` | MEDIUM | P1 |
| 17.12 | Validate YAML config permissions | `services/embeddings.py` | MEDIUM | P1 |
| 17.13 | Fix deprecated datetime.utcnow() calls | `services/*.py` | MEDIUM | P1 |

#### Tasks - Low Priority

| ID | Task | File(s) | Severity | Priority |
|----|------|---------|----------|----------|
| 17.14 | Add ReDoS timeout protection | `services/job_parser.py` | LOW | P2 |
| 17.15 | Improve filename sanitization | `routers/*.py` | LOW | P2 |
| 17.16 | Add database encryption at rest | `db/database.py` | LOW | P2 |

#### Acceptance Criteria
- [ ] All P0 security issues resolved
- [ ] JWT authentication working for all endpoints
- [ ] Rate limiting prevents abuse (10 req/min default)
- [ ] No sensitive data in error responses
- [ ] CORS restricted to specific origins/methods
- [ ] Security scan (bandit) passes with no high-severity issues
- [ ] Dependency scan (safety) passes

#### Security Scanning Commands
```bash
# Code vulnerability scanning
pip install bandit safety
bandit -r backend/ -ll
safety check

# Dependency audit
pip-audit
```

---

### Sprint 19: Deployment (PRD 6.5)

**Goal:** Deploy to Railway (backend) and Vercel (frontend).

**Prerequisite:** Sprint 18 (Production Hardening) must be complete.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 18.1 | Create Railway project | - | 6.5 | P0 |
| 18.2 | Configure backend deployment | `railway.toml` | 6.5 | P0 |
| 18.3 | Set up environment variables (secrets) | Railway dashboard | 6.9 | P0 |
| 18.4 | Configure Qdrant for production | - | 6.5 | P1 |
| 18.5 | Create Vercel project | - | 6.5 | P0 |
| 18.6 | Configure frontend deployment | `vercel.json` | 6.5 | P0 |
| 18.7 | Set up custom domain | Vercel/Railway | 6.5 | P2 |
| 18.8 | Configure production CORS | `backend/main.py` | 6.5 | P0 |
| 18.9 | Add health check endpoints | `backend/routers/health.py` | 6.8 | P1 |
| 18.10 | Write deployment documentation | `docs/DEPLOYMENT.md` | - | P1 |
| 18.11 | Set up monitoring/alerting | - | 6.8 | P1 |
| 18.12 | Configure backup strategy | - | - | P1 |

---

## Dependencies & Prerequisites

### External Dependencies
- **Anthropic API Key** - For Claude LLM calls
- **OpenAI API Key** - For embeddings (or alternative)
- **Qdrant** - Local instance for development, cloud for production

### Internal Dependencies
```
Sprint 2 (Skill Gap) → depends on → Sprint 1 (Critic) ✅
Sprint 3 (CL Critic) → depends on → Sprint 1 (Critic) ✅
Sprint 4 (Schema Migration) → depends on → Sprint 1-3 (Core complete) ✅
Sprint 5 (Rewriting) → depends on → Sprint 4 (Schema)
Sprint 8 (Learning) → depends on → Sprint 7 (Qdrant)
Sprint 10 (UI) → depends on → Sprint 9 (Next.js setup)
Phase 2 → depends on → Phase 1A complete ✅
Phase 3 → depends on → Phase 1E complete
Sprint 18 (Security) → depends on → Phase 1A complete ✅
Sprint 19 (Deployment) → depends on → Sprint 18 (Security)
```

---

## Success Metrics

### Phase 1 Complete
- [ ] Resume generation < 60 seconds
- [ ] ATS score > 75 for all outputs
- [ ] Zero banned phrases in outputs
- [ ] All outputs pass critic evaluation
- [ ] Skill-gap analysis accurate and actionable

### Phase 2 Complete
- [ ] Company enrichment for 80%+ of job postings
- [ ] Hiring manager inference with confidence scores
- [ ] Warm contacts identified when data available
- [ ] Outreach messages ready to send

### Phase 3 Complete
- [ ] Application status tracked end-to-end
- [ ] Contact history maintained
- [ ] Task reminders functional
- [ ] Deployed and accessible via URL

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucination in bullets | High | Strict validation, fact-checking prompts |
| ATS scoring inaccuracy | Medium | Benchmark against real ATS systems |
| Qdrant performance at scale | Low | Local testing sufficient for single user |
| LinkedIn compliance | Medium | User-pasted data only, no scraping |
| API rate limits | Medium | Caching, batching, fallback models |

---

## Appendix: File Structure (Target)

```
etps/
├── backend/
│   ├── config/
│   │   ├── config.yaml
│   │   └── constants.py
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── migrations/
│   ├── routers/
│   │   ├── applications.py
│   │   ├── company.py
│   │   ├── contacts.py
│   │   ├── cover_letter.py
│   │   ├── job.py
│   │   ├── networking.py
│   │   ├── outputs.py
│   │   ├── resume.py
│   │   └── tasks.py
│   ├── schemas/
│   │   ├── cover_letter.py
│   │   ├── critic.py
│   │   ├── job_parser.py
│   │   ├── resume_tailor.py
│   │   └── skill_gap.py
│   ├── services/
│   │   ├── ats_scorer.py
│   │   ├── bullet_rewriter.py
│   │   ├── company_enrichment.py
│   │   ├── contact_matcher.py
│   │   ├── cover_letter.py
│   │   ├── cover_letter_critic.py
│   │   ├── docx_cover_letter.py
│   │   ├── docx_resume.py
│   │   ├── embeddings.py
│   │   ├── hiring_manager.py
│   │   ├── job_parser.py
│   │   ├── networking.py
│   │   ├── outreach.py
│   │   ├── output_retrieval.py
│   │   ├── resume_critic.py
│   │   ├── resume_tailor.py
│   │   ├── skill_gap.py
│   │   ├── style_enforcer.py
│   │   ├── text_cover_letter.py
│   │   ├── text_resume.py
│   │   └── vector_store.py
│   ├── tests/
│   │   └── ...
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   └── ...
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── DEPLOYMENT.md
│   └── ...
└── ETPS_PRD.md
```

---

*Last Updated: December 2025*

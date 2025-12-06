# ETPS Implementation Plan
**Full PRD Implementation Roadmap**
**Version 1.2 — December 2025**
*Merged content from IMPLEMENTATION_ROADMAP.md (v1.3.0 Schema)*

---

## Executive Summary

This document provides a detailed implementation plan to build ETPS to full PRD specification. The plan is organized into sprints with specific tasks, acceptance criteria, and dependencies.

**Current State:** Phase 1A complete with Resume Critic, Skill-Gap Analysis, and Cover Letter Critic implemented.

**Target State:** Full Phase 1 (Core Quality), Phase 2 (Company Intelligence), and Phase 3 (Application Tracking) as defined in ETPS_PRD.md.

### Runtime Pipeline Reference

All sprints (5–10 and beyond) assume the authoritative runtime pipeline defined in **PRD Section 1.6**. This pipeline governs the end-to-end flow for each job application:

1. Job Intake → 2. JD Parsing → 3. Company Enrichment → 4. Fit & Skill-Gap Analysis → 5. Bullet & Content Selection → 6. Summary Rewrite → 7. Resume Construction → 8. Cover Letter Generation → 9. Critic & Refinement Loop → 10. Rendering & Output

Refer to `ETPS_PRD.md` Section 1.6 for the full specification.

---

## Progress Summary

| Sprint | Status | Completion Date | Notes |
|--------|--------|-----------------|-------|
| Sprint 1: Resume Critic Agent | ✅ COMPLETE | Dec 2025 | Full critic loop with iteration, ATS scoring, style enforcement |
| Sprint 2: Skill-Gap Analysis | ✅ COMPLETE | Dec 2025 | Semantic matching with OpenAI embeddings, positioning strategies |
| Sprint 3: Cover Letter Critic | ✅ COMPLETE | Dec 2025 | Critic iteration loop, banned phrase detection, LLM revision |
| Sprint 4: Schema & Data Migration | ✅ COMPLETE | Dec 2025 | v1.3.0 schema, engagement structure, 8 engagements |
| Sprint 5: Bullet Rewriting & Selection | ✅ COMPLETE | Dec 2025 | LLM-powered rewriting, bullet selection algorithm, truthfulness checks |
| Sprint 5B: Summary Rewrite Engine | ✅ COMPLETE | Dec 2025 | Summary rewrite with candidate_profile, 60-word limit, critic validation |
| Sprint 6: Version History & Plain Text | ✅ COMPLETE | Dec 2025 | Plain text output, format param, version history API, DOCX refinements |
| Sprint 7: Qdrant Integration | ✅ COMPLETE | Dec 2025 | Vector store service, MockVectorStore, bullet/job indexing, semantic search |
| Sprint 8: Learning from Approved Outputs | ✅ COMPLETE | Dec 2025 | ApprovedOutput model, output approval API, similarity retrieval, vector indexing |
| Sprint 8B: Gap Remediation | ✅ COMPLETE | Dec 2025 | Integration gaps, truthfulness validation, skill-gap connection |
| Sprint 8C: Pagination-Aware Layout | 🔲 NOT STARTED | - | Line budgeting, value-per-line allocation, page split rules |
| Sprint 9-10: Frontend MVP | 🔲 NOT STARTED | - | Next.js + Job Intake UI |
| Sprint 11-14: Company Intelligence | 🔲 NOT STARTED | - | Phase 2 |
| Sprint 15-17: Application Tracking | 🔲 NOT STARTED | - | Phase 3 |
| Sprint 18: Production Hardening | 🔲 NOT STARTED | - | ⚠️ Security & reliability (8 P0 tasks) |
| Sprint 19: Deployment | 🔲 NOT STARTED | - | Railway + Vercel |

### Test Coverage
- **Total Tests:** 258 passing
- **Test Files:** test_bullet_rewriter.py, test_truthfulness_check.py, test_summary_rewrite.py, test_text_output.py, test_vector_store.py, test_approved_outputs.py, test_sprint_8b_integration.py
- **Coverage:** All Sprint 1-8B functionality tested

### Git Workflow & Commit Checkpoints

**Repository:** https://github.com/blackbenjamin/etps

**Commit Convention:** Commits are made at these checkpoints:

| Checkpoint | Commit Message Format | Example |
|------------|----------------------|---------|
| Sprint complete | `feat(sprint-N): <summary>` | `feat(sprint-3): Implement Cover Letter Critic` |
| Bug fix batch | `fix: <summary>` | `fix: Resolve embedding dimension mismatch` |
| Documentation update | `docs: <summary>` | `docs: Update implementation plan progress` |
| Config/setup change | `chore: <summary>` | `chore: Add .gitignore for .env` |

**Commit Timing:**
- ✅ After each sprint is complete (all tests passing)
- ✅ After significant bug fix sessions
- ✅ After major documentation updates
- ✅ Before switching to a different sprint/task

**Pre-Push Checklist (mandatory before every push):**
```bash
cd /Users/benjaminblack/projects/etps/backend

# 1. Run all unit tests
python -m pytest -v --tb=short

# 2. Security scan (code vulnerabilities)
pip install bandit 2>/dev/null; bandit -r . -ll --exclude ./test*.py

# 3. Dependency audit
pip install safety 2>/dev/null; safety check

# 4. Verify no secrets in staged files
git diff --cached --name-only | xargs grep -l -E "(api_key|secret|password)" || echo "✓ No secrets"
```
All checks must pass before `git push`.

**Commit History:**
| Commit | Sprint | Description |
|--------|--------|-------------|
| `9f8a8c5` | - | Git workflow conventions |
| `5c7fe89` | 3,4 | Cover Letter Critic + rename + Schema Migration |
| `37738df` | 2 | Tune embedding threshold |
| `ce14e48` | 2 | Skill Gap Analyzer enhancements |
| `eca075f` | 1 | Resume Critic Agent |
| `96ce919` | - | Initial implementation plan |

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
│ PHASE 1C: LLM Enhancement (Sprints 5-5B-6)                     │
│ - Bullet Rewriting & Selection Algorithm                        │
│ - Summary Rewrite Engine (Sprint 5B)                            │
│ - Truthfulness Consistency Checks                               │
│ - Version History                                               │
│ - Text/Plain Output                                             │
│ - DOCX Template Refinement                                      │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1D: Vector Search & Learning (Sprints 7-8-8B)            │
│ - Qdrant Integration                                            │
│ - Semantic Bullet Matching                                      │
│ - Learning from Approved Outputs                                │
│ - Gap Remediation (Sprint 8B)                                   │
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

### Sprint 5: Bullet Rewriting & Selection (PRD 2.4, 2.6, 2.8, 2.9, 4.3)

**Goal:** Implement LLM-powered bullet rewriting, deterministic bullet selection algorithm, engagements nesting, and truthfulness checks to optimize resumes for JD keywords while preserving truth.

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
| 1.4.10 | Implement deterministic bullet selection algorithm using structured inputs (domain_tags_master, tech_tags, ai_portfolio, seniority tags, importance flags) as defined in PRD 2.8 | `services/resume_tailor.py` | PRD 2.8 | P0 |
| 1.4.11 | Integrate portfolio project bullets when JD is AI/LLM-heavy | `services/resume_tailor.py` | PRD 2.8 | P1 |
| 1.4.12 | Ensure resume_tailor JSON output nests engagements under consulting experiences | `services/resume_tailor.py`, `schemas/resume_tailor.py` | PRD 2.9 | P0 |
| 1.4.13 | Implement resume truthfulness consistency check | `services/resume_critic.py` | PRD 4.3 | P0 |

#### Acceptance Criteria
- [ ] Bullets rewritten to include JD keywords
- [ ] Original text preserved in version history
- [ ] No factual changes (dates, metrics, employers)
- [ ] STAR notes used to enrich rewrites when available
- [ ] Rewriting can be enabled/disabled per request
- [ ] Bullet selection follows PRD 2.8 algorithm (tags + importance + role relevance)
- [ ] Consulting engagements limited to most relevant clients per job
- [ ] Redundant bullets minimized across roles
- [ ] Resume Critic validates factual consistency (employers, titles, dates, locations) against stored employment_history data

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

### Sprint 5B: Summary Rewrite Engine (PRD 2.10) ✅ COMPLETE

**Goal:** Implement a summary rewriting module that tailors the professional summary to each job while enforcing tone and banned phrase rules.

**Status:** ✅ Completed December 2025

#### Tasks

| ID | Task | File(s) | PRD Ref | Status |
|----|------|---------|---------|--------|
| 5B.1 | Design summary rewrite prompt template | `services/llm/prompts/summary_rewrite.txt` | 2.10 | ✅ |
| 5B.2 | Implement SummaryRewriteService | `services/summary_rewrite.py` | 2.10 | ✅ |
| 5B.3 | Integrate with resume_tailor pipeline | `services/resume_tailor.py` | 1.6, 2.10 | ✅ |
| 5B.4 | Enforce banned phrases and tone via critic | `services/critic.py` | 4.8 | ✅ |
| 5B.5 | Add unit tests for summary rewrite | `tests/test_summary_rewrite.py` | 2.10 | ✅ |

#### Acceptance Criteria
- [x] Summary rewritten per job using job_profile core priorities
- [x] Summary respects word limit (60 words) and banned phrases
- [x] Critic fails outputs with stale or non-tailored summaries

#### Implementation Notes
- `services/summary_rewrite.py` - Core rewrite service (~340 lines)
- Uses `candidate_profile.primary_identity`, `specializations`, and `target_roles`
- Integrates `company_profile` context when available (future Phase 2)
- `validate_summary_quality()` function added to critic.py
- 53 unit tests passing

---

### Sprint 6: Version History & Plain Text (PRD 2.5, 2.6) ✅ COMPLETE

**Goal:** Implement bullet version history and text/plain output format.

**Status:** ✅ Completed December 2025

#### Tasks

| ID | Task | File(s) | PRD Ref | Status |
|----|------|---------|---------|--------|
| 1.6.1 | Design version history JSON schema | `db/models.py` | 2.6 | ✅ (Sprint 5) |
| 1.6.2 | Implement version tracking on save | `services/bullet_rewriter.py` | 2.6 | ✅ (Sprint 5) |
| 1.6.3 | Add version history retrieval API | `routers/resume.py` | 2.6 | ✅ |
| 1.6.4 | Implement plain text resume generator | `services/text_resume.py` | 2.5 | ✅ |
| 1.6.5 | Implement plain text cover letter generator | `services/text_cover_letter.py` | 2.5 | ✅ |
| 1.6.6 | Add output format selection to API | `routers/resume.py`, `routers/cover_letter.py` | 2.5 | ✅ |
| 1.6.7 | Write unit tests | `tests/test_text_output.py` | - | ✅ |
| 1.6.8 | Refine DOCX resume template | `services/docx_resume.py` | PRD 2.3, 2.5 | ✅ |

#### Acceptance Criteria
- [x] All bullet rewrites stored in version history (done in Sprint 5)
- [x] Version history includes timestamp, context, original ref
- [x] Plain text output ATS-friendly (ASCII only, no special characters)
- [x] API supports format param: docx, text, json
- [x] Header shows name, contact line, and portfolio URL
- [x] Skills section appears in correct position (before Education)
- [x] No unexpected line breaks or misaligned bullets

#### Implementation Notes
- `services/text_resume.py` - ATS-friendly plain text (~280 lines)
- `services/text_cover_letter.py` - Business letter format (~145 lines)
- API format parameter: `?format=docx|text|json` with docx as default
- GET `/resume/bullets/{id}/versions` for version history
- 64 unit tests in test_text_output.py

---

## Phase 1D: Vector Search & Learning

### Sprint 7: Qdrant Integration (PRD 6.3) ✅ COMPLETE

**Goal:** Set up Qdrant vector store for semantic search.

**Status:** ✅ Completed December 2025

#### Tasks

| ID | Task | File(s) | PRD Ref | Status |
|----|------|---------|---------|--------|
| 1.7.1 | Add Qdrant to requirements | `requirements.txt` | 6.3 | ✅ |
| 1.7.2 | Create Qdrant client wrapper | `services/vector_store.py` | 6.3 | ✅ |
| 1.7.3 | Define collection schemas | `services/vector_store.py` | 6.3 | ✅ |
| 1.7.4 | Implement bullet embedding generation | `services/embeddings.py` | 6.3 | ✅ |
| 1.7.5 | Implement job profile embedding | `services/embeddings.py` | 6.3 | ✅ |
| 1.7.6 | Create bullet indexing service | `services/vector_store.py` | 6.3 | ✅ |
| 1.7.7 | Create job similarity search | `services/vector_store.py` | 6.3 | ✅ |
| 1.7.8 | Add embedding model config | `config/config.yaml` | 6.4 | ✅ |
| 1.7.9 | Write integration tests | `tests/test_vector_store.py` | - | ✅ |

#### Acceptance Criteria
- [x] MockVectorStore for testing with in-memory cosine similarity
- [x] QdrantVectorStore for production (when Qdrant server available)
- [x] All bullets indexed with embeddings via `index_bullet()` / `index_all_bullets()`
- [x] Job profiles indexed via `index_job_profile()`
- [x] Semantic search returns relevant bullets via `search_similar_bullets()` / `search_bullets_for_job()`
- [x] Filter field validation for security

#### Implementation Notes
- `services/vector_store.py` - Complete vector store service (~1000 lines)
- `BaseVectorStore` abstract class with `QdrantVectorStore` and `MockVectorStore` implementations
- Collection schemas: bullets, jobs, approved_outputs (ready for Sprint 8)
- Factory function: `create_vector_store(use_mock=bool)`
- New embedding methods: `embed_bullet()`, `embed_job_profile()`
- 54 unit tests passing in test_vector_store.py

#### Collections
```
etps_bullets: {id, text, embedding, tags, experience_id, usage_count, importance, ai_first_choice, seniority_level}
etps_jobs: {id, title, embedding, company, requirements, seniority, job_type_tags}
etps_approved_outputs: {id, type, embedding, job_context, content} (Sprint 8)
```

---

### Sprint 8: Learning from Approved Outputs (PRD 4.7)

**Goal:** Store approved outputs and retrieve similar examples for new requests.

**Status:** ✅ COMPLETE - Infrastructure complete, integration implemented in Sprint 8B

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority | Status |
|----|------|---------|---------|----------|--------|
| 1.8.1 | Create ApprovedOutput model | `db/models.py` | 4.7 | P0 | ✅ |
| 1.8.2 | Implement output approval API | `routers/outputs.py` | 4.7 | P0 | ✅ |
| 1.8.3 | Index approved outputs in Qdrant | `services/vector_store.py` | 4.7 | P0 | ✅ |
| 1.8.4 | Implement similar output retrieval | `services/output_retrieval.py` | 4.7 | P0 | ✅ |
| 1.8.5 | Integrate examples into generation prompts | `services/resume_tailor.py`, `services/cover_letter.py` | 4.7 | P1 | ❌ Moved to 8B |
| 1.8.6 | Add quality comparison in critic | `services/critic.py` | 4.7 | P2 | ❌ Deferred |
| 1.8.7 | Write unit tests | `tests/test_approved_outputs.py` | - | P1 | ✅ |

#### Acceptance Criteria
- [x] Users can approve generated outputs
- [x] Approved outputs indexed with metadata
- [x] Similar examples retrieved for new jobs → Completed in Sprint 8B
- [x] Examples guide generation without copy-paste → Completed in Sprint 8B

#### Implementation Notes
- 45 unit tests in test_approved_outputs.py
- ApprovedOutput model with user, application, job_profile relationships
- POST /outputs/approve and GET /outputs/similar endpoints
- index_approved_output() function in vector_store.py
- output_retrieval.py service with format_examples_for_prompt()
- **Gap Resolved:** Integration into generation pipeline completed in Sprint 8B

---

### Sprint 8B: Gap Remediation (PRD Integration Gaps)

**Goal:** Address critical integration gaps identified in post-Sprint 8 review. Complete the learning system integration and add missing validations.

**Status:** ✅ COMPLETE - All integration gaps resolved.

**Reference:** See `docs/GAP_ANALYSIS_SPRINT_8_REVIEW.md` for full gap analysis.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority | Status |
|----|------|---------|---------|----------|--------|
| 8B.1 | Integrate approved bullets into resume generation | `services/resume_tailor.py` | 4.7 | P0 | ✅ |
| 8B.2 | Integrate approved paragraphs into cover letter generation | `services/cover_letter.py` | 4.7 | P0 | ✅ |
| 8B.3 | Integrate skill gap results into bullet selection | `services/resume_tailor.py` | 1.6, 2.8 | P0 | ✅ |
| 8B.4 | Implement truthfulness validation in resume critic | `services/critic.py` | 4.3 | P0 | ✅ |
| 8B.5 | Add em-dash detection to resume critic | `services/critic.py` | 3.5, 4.3 | P1 | ✅ |
| 8B.6 | Add max_iterations to config.yaml | `config/config.yaml` | 4.4 | P2 | ✅ |
| 8B.7 | Pass STAR notes to bullet rewriter | `services/bullet_rewriter.py` | 2.6 | P2 | ✅ |
| 8B.8 | Thread context_notes to summary rewrite | `services/summary_rewrite.py` | 1.3 | P2 | ✅ |
| 8B.9 | Verify portfolio integration end-to-end | `services/resume_tailor.py` | 2.8 | P1 | ✅ |
| 8B.10 | Write integration tests for new connections | `tests/test_sprint_8b_integration.py` | - | P1 | ✅ |

#### Acceptance Criteria
- [x] Similar approved bullets retrieved and formatted for LLM prompt during resume generation
- [x] Similar approved paragraphs retrieved for cover letter generation
- [x] Skill gap positioning_angles influence bullet selection scoring
- [x] Resume critic validates employer names, titles, dates against stored data
- [x] Resume critic detects and fails on em-dashes
- [x] max_iterations configurable via config.yaml
- [x] STAR notes passed to bullet rewrite prompt when available
- [x] context_notes/custom_instructions passed to summary rewrite
- [x] Portfolio bullets integrated for AI-heavy jobs
- [x] All new integrations have test coverage (15 tests in test_sprint_8b_integration.py)

#### Implementation Notes
- resume_tailor.py: Added `enable_learning` parameter, retrieves similar approved bullets, formats for prompt
- cover_letter.py: Added `enable_learning` parameter, retrieves similar approved paragraphs
- resume_tailor.py: Skill gap positioning_angles and user_advantages used as bonus scores in bullet selection
- critic.py: `validate_resume_truthfulness()` validates all experience fields against database
- critic.py: `check_em_dashes()` called in `evaluate_resume()` for summary and bullets
- config.yaml: Already had `max_iterations: 3`, services now read from config
- bullet_rewriter.py: Already passes STAR notes when `strategy="both"` or `strategy="star_enrichment"`
- summary_rewrite.py: Added `context_notes` parameter, appended to LLM prompt
- resume_tailor.py: `is_ai_heavy_job()` and `get_portfolio_bullets()` work end-to-end

---

### Sprint 8C: Pagination-Aware Layout & Page Budgeting (PRD 2.11)

**Goal:** Implement pagination-aware resume layout that allocates bullets under a global space budget, avoids orphaned job headers, and enables optional bullet compression.

**Status:** 🔲 NOT STARTED

**Reference:** See PRD Section 2.11 for full specification.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 8C.1 | Add pagination constants to config.yaml (page1_line_budget, page2_line_budget, chars_per_line_estimate, min_bullets_per_role, max_bullets_per_role) | `config/config.yaml` | 2.11 | P0 |
| 8C.2 | Implement line budget cost estimator for bullets, headers, summary, and skills | `services/resume_tailor.py`, `services/pagination.py` | 2.11 | P0 |
| 8C.3 | Implement global space-aware bullet allocation algorithm (value-per-line prioritization) | `services/resume_tailor.py`, `services/pagination.py` | 2.8, 2.11 | P0 |
| 8C.4 | Implement job–page split simulation and rules to avoid orphaned job headers and single bullets | `services/pagination.py` | 2.11 | P0 |
| 8C.5 | Add per-role minimum/maximum bullet constraints with role condensation for older roles | `services/resume_tailor.py` | 2.11 | P0 |
| 8C.6 | Implement optional bullet compression mode (shortening long bullets within truthfulness constraints) | `services/bullet_rewriter.py`, `services/resume_tailor.py` | 2.11, 4.3 | P1 |
| 8C.7 | Update SummaryRewriteService to accept max_lines hint derived from Page 1 budget | `services/summary_rewrite.py`, `services/resume_tailor.py` | 2.10, 2.11 | P0 |
| 8C.8 | Add basic pagination sanity checks to resume critic (no orphaned headers, no single-bullet orphans) | `services/critic.py` | 4.3, 2.11 | P1 |
| 8C.9 | Add unit tests for space-aware allocation and job split behavior | `tests/test_pagination_allocation.py` | 2.11 | P1 |
| 8C.10 | Add regression tests for pagination-aware allocation with sample resumes | `tests/test_pagination_regression.py` | 2.11 | P2 |

#### Acceptance Criteria
- [ ] Resume bullet selection respects a global line budget for Page 1 and Page 2
- [ ] No job header is placed as the last element on a page with zero bullets below it (per simulation)
- [ ] Older / less relevant roles are automatically condensed first when space is constrained
- [ ] Optional bullet compression reduces overflow while preserving truthfulness and tone
- [ ] SummaryRewriteService can shorten or slightly expand the summary based on a max-lines hint derived from the Page 1 budget
- [ ] Resume critic validates basic pagination sanity (no orphaned job headers)
- [ ] All pagination logic has test coverage

#### Estimated Effort
- P0 tasks: 12-16 hours
- P1 tasks: 6-8 hours
- P2 tasks: 2-3 hours
- **Total:** ~22 hours

#### Design Notes

**Line Budget Estimation:**
```python
# Each element has an estimated line cost
SECTION_HEADER_LINES = 1
JOB_HEADER_LINES = 2  # company, title, location, dates
BULLET_CHROME_LINES = 1  # bullet point itself
CHARS_PER_LINE = 75  # configurable

def estimate_bullet_lines(bullet_text: str) -> int:
    """Estimate lines for a single bullet."""
    text_lines = math.ceil(len(bullet_text) / CHARS_PER_LINE)
    return BULLET_CHROME_LINES + text_lines
```

**Value-Per-Line Prioritization:**
```python
# For each bullet, compute value_per_line
value_per_line = relevance_score / estimated_lines
# Sort bullets by value_per_line descending when space is constrained
```

**Page Split Simulation:**
```python
# Fill Page 1 and Page 2 using line budget
# If job header would be on last 2 lines of Page 1:
#   Option A: Move entire job to Page 2
#   Option B: Reduce bullets in earlier roles to make room
```

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
| 1.10.9 | Add ATS score display with color coding and brief explanation | `frontend/src/components/ATSScoreCard.tsx` | PRD 1.4, 4.3 | P1 |
| 1.10.10 | Wire up to backend APIs | `frontend/src/app/page.tsx` | 6.6 | P0 |
| 1.10.11 | Pass context notes from UI to backend generation endpoints | `frontend/src/app/page.tsx`, `backend/routers/resume.py`, `backend/routers/cover_letter.py` | PRD 1.6, 6.6 | P0 |

#### Acceptance Criteria
- [ ] User can paste JD text or URL
- [ ] Generate buttons trigger backend calls
- [ ] Download buttons work for all formats
- [ ] Skill-gap analysis displayed clearly
- [ ] ATS score shown with numeric score (0-100), color coding (red/yellow/green), and brief explanation
- [ ] Context notes field available and passed to backend generation endpoints

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

#### Implementation Notes
- Ensure company enrichment outputs include `ai_maturity` and `culture_signals` fields (PRD 5.10)
- These fields influence resume bullet selection, summary rewriting, and cover letter generation

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
| 2.4.11 | Implement safety guardrails for outreach suggestions (avoid overreaching senior contacts, label low-confidence inferences) | `services/networking.py`, `services/outreach.py` | PRD 5.9 | P0 |

#### Implementation Notes
- `company_profile` also influences resume and cover letter selection/phrasing (PRD 5.10)
- Networking guardrails must avoid recommending outreach to C-level executives unless role is clearly senior enough and user explicitly opts in
- Label any inferred org structure or reporting lines with confidence levels

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
Sprint 5 (Rewriting) → depends on → Sprint 4 (Schema) ✅
Sprint 8 (Learning) → depends on → Sprint 7 (Qdrant) ✅
Sprint 8B (Gap Remediation) → depends on → Sprint 8 (Learning) ✅
Sprint 8C (Pagination) → depends on → Sprint 8B (Gap Remediation) ✅
Sprint 9 (Frontend) → depends on → Sprint 8C (Pagination)
Sprint 10 (UI) → depends on → Sprint 9 (Next.js setup)
Phase 2 → depends on → Phase 1E complete
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

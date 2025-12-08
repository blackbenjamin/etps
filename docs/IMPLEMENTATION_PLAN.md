# ETPS Implementation Plan
**Full PRD Implementation Roadmap**
**Version 1.3 — December 2025**
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
| Sprint 8C: Pagination-Aware Layout | ✅ COMPLETE | Dec 2025 | Line budgeting, value-per-line allocation, page split rules, security hardening |
| Sprint 9-10: Frontend MVP | ✅ COMPLETE | Dec 2025 | Next.js + Job Intake UI, Zustand, TanStack Query, shadcn/ui |
| Sprint 10B: JD Extraction Quality | ✅ COMPLETE | Dec 2025 | URL extraction validation, parser improvements, user-friendly errors |
| Sprint 10C: Parser & Skill Gap Fixes | ✅ COMPLETE | Dec 2025 | Company/Title/Location extraction, skill gap score calculation fix |
| Sprint 10D: Debugging & Improvements | ✅ COMPLETE | Dec 2025 | Mock services audit, skill mappings, frontend fixes, user profile enrichment |
| Sprint 10E: Interactive Skill Selection | ✅ COMPLETE | Dec 2025 | Drag-drop skill panel, key skills for cover letter |
| Sprint 11: Capability-Aware Skill Extraction | 🔄 IN PROGRESS | - | LLM-based capability clusters, evidence mapping |
| Sprint 12-15: Company Intelligence | 🔲 NOT STARTED | - | Phase 2 |
| Sprint 16-18: Application Tracking | 🔲 NOT STARTED | - | Phase 3 |
| Sprint 19: Production Hardening | 🔲 NOT STARTED | - | ⚠️ Security & reliability (8 P0 tasks) |
| Sprint 20: Deployment | 🔲 NOT STARTED | - | Railway + Vercel |

### Test Coverage
- **Total Tests:** 560 passing
- **Test Files:** test_bullet_rewriter.py, test_truthfulness_check.py, test_summary_rewrite.py, test_text_output.py, test_vector_store.py, test_approved_outputs.py, test_sprint_8b_integration.py, test_pagination_allocation.py, test_sprint_8c_regression.py, test_job_parser_extraction.py, test_skill_selection.py
- **Coverage:** All Sprint 1-10E functionality tested

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
│ PHASE 1E: Frontend MVP (Sprints 9-10D)              ✅ COMPLETE │
│ - Next.js Setup                                     ✅          │
│ - Job Intake Page                                   ✅          │
│ - Generate & Download Workflow                      ✅          │
│ - Skill-Gap Display                                 ✅          │
│ - JD Extraction Quality Validation (Sprint 10B)    ✅          │
│ - Debugging & Improvements (Sprint 10D)            ✅          │
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

**Status:** ✅ COMPLETE (Dec 2025)

**Reference:** See PRD Section 2.11 for full specification.

#### Tasks

| ID | Task | File(s) | PRD Ref | Status |
|----|------|---------|---------|--------|
| 8C.1 | Add pagination constants to config.yaml | `config/config.yaml` | 2.11 | ✅ |
| 8C.2 | Implement line budget cost estimator | `services/pagination.py` | 2.11 | ✅ |
| 8C.3 | Implement value-per-line bullet allocation | `services/pagination.py` | 2.8, 2.11 | ✅ |
| 8C.4 | Implement PageSplitSimulator | `services/pagination.py` | 2.11 | ✅ |
| 8C.5 | Add per-role constraints and condensation | `services/resume_tailor.py` | 2.11 | ✅ |
| 8C.6 | Implement bullet compression mode | `services/bullet_rewriter.py`, `services/pagination.py` | 2.11, 4.3 | ✅ |
| 8C.7 | Add max_lines hint to summary_rewrite | `services/summary_rewrite.py` | 2.10, 2.11 | ✅ |
| 8C.8 | Add pagination sanity checks to critic | `services/critic.py` | 4.3, 2.11 | ✅ |
| 8C.9 | Add unit tests (44 tests) | `tests/test_pagination_allocation.py` | 2.11 | ✅ |
| 8C.10 | Add regression tests (42 tests) | `tests/test_sprint_8c_regression.py` | 2.11 | ✅ |

#### Acceptance Criteria
- [x] Resume bullet selection respects a global line budget for Page 1 and Page 2
- [x] No job header is placed as the last element on a page with zero bullets below it (per simulation)
- [x] Older / less relevant roles are automatically condensed first when space is constrained
- [x] Optional bullet compression reduces overflow while preserving truthfulness and tone
- [x] SummaryRewriteService can shorten or slightly expand the summary based on a max-lines hint derived from the Page 1 budget
- [x] Resume critic validates basic pagination sanity (no orphaned job headers)
- [x] All pagination logic has test coverage (86 new tests)

#### Security Hardening (Post-Review)
- Pre-compiled regex patterns to prevent ReDoS attacks
- Input length validation (500 char max for compression)
- Bounds checking on max_lines parameter (1-100)
- Improved exception handling with specific error types
- Parameter validation moved to function start
- Condensation suggestion validation before array access

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
- [x] User can paste JD text or URL
- [x] Generate buttons trigger backend calls
- [x] Download buttons work for all formats
- [x] Skill-gap analysis displayed clearly
- [x] ATS score shown with numeric score (0-100), color coding (red/yellow/green), and brief explanation
- [x] Context notes field available and passed to backend generation endpoints

---

### Sprint 10B: JD Extraction Quality & Parser Improvements ✅ COMPLETE

**Goal:** Implement automatic quality validation for URL-based job description extraction, improve job parser accuracy, and provide user-friendly error messages when extraction fails.

**Status:** ✅ Completed December 2025

#### Tasks

| ID | Task | File(s) | PRD Ref | Status |
|----|------|---------|---------|--------|
| 10B.1 | Add ExtractionQuality dataclass | `utils/text_processing.py` | 1.6 | ✅ |
| 10B.2 | Implement validate_extraction_quality() | `utils/text_processing.py` | 1.6 | ✅ |
| 10B.3 | Add ExtractionFailedError exception | `utils/text_processing.py` | 1.6 | ✅ |
| 10B.4 | Add URL normalization (Lever, Greenhouse) | `utils/text_processing.py` | 1.6 | ✅ |
| 10B.5 | Add EEO/boilerplate content filtering | `utils/text_processing.py` | 1.6 | ✅ |
| 10B.6 | Add meta tag extraction for JS-rendered pages | `utils/text_processing.py` | 1.6 | ✅ |
| 10B.7 | Update job parser exception handling | `services/job_parser.py` | 1.6 | ✅ |
| 10B.8 | Add SECTION_STOP_PATTERNS for parser | `services/job_parser.py` | 2.7 | ✅ |
| 10B.9 | Fix nice-to-have header patterns | `services/job_parser.py` | 2.7 | ✅ |
| 10B.10 | Remove HTTPS from skills taxonomy | `services/job_parser.py` | 2.7 | ✅ |
| 10B.11 | Add API error handler for ExtractionFailedError | `routers/job.py` | 1.6 | ✅ |
| 10B.12 | Add ExtractionFailedError to frontend API | `frontend/src/lib/api.ts` | 6.6 | ✅ |
| 10B.13 | Update JobIntakeForm error display | `frontend/src/components/job-intake/JobIntakeForm.tsx` | 6.6 | ✅ |

#### Acceptance Criteria
- [x] URL extraction validates content quality (length, job keywords, error indicators)
- [x] Extraction quality score computed (0-100) with configurable threshold (50)
- [x] ExtractionFailedError raised with user-friendly message when quality too low
- [x] Lever/Greenhouse /apply URLs normalized to job description pages
- [x] EEO statements and legal boilerplate filtered from extraction
- [x] Meta tags extracted as fallback for JS-rendered pages
- [x] API returns HTTP 422 with structured error for extraction failures
- [x] Frontend displays amber warning with suggestion to paste JD text directly
- [x] Job parser stops at salary/benefits/success metrics sections
- [x] Nice-to-have patterns don't match mid-sentence "preferred"
- [x] Skills taxonomy doesn't match false positives from URLs (HTTPS removed)

#### Implementation Notes
- `ExtractionQuality` dataclass with `is_valid`, `score`, `issues`, `suggestions`
- Quality checks: minimum length, job keywords, error indicators (login walls, CAPTCHA, etc.), boilerplate ratio, skill indicators
- `SECTION_STOP_PATTERNS` added to stop parsing at salary, benefits, success metrics, EEO sections
- Frontend shows distinct amber warning for extraction failures vs. red error for other failures
- All 432 tests passing

---

### Sprint 10D: Debugging & Improvements ✅ COMPLETE

**Goal:** Address various debugging issues, audit mock services, improve skill matching, and enhance frontend UX.

**Status:** ✅ Completed December 2025

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 10D.1 | Audit mock services usage across codebase | All services | ✅ |
| 10D.2 | Document mock vs live service status | `docs/IMPLEMENTATION_PLAN.md` | ✅ |
| 10D.3 | Add AI/consulting skill similarity mappings | `services/embeddings.py` | ✅ |
| 10D.4 | Fix user_id defaulting to 2 in frontend API | `frontend/src/lib/api.ts` | ✅ |
| 10D.5 | Enhance company name extraction patterns | `services/job_parser.py` | ✅ |
| 10D.6 | Add editable company name field in frontend | `frontend/src/app/page.tsx` | ✅ |
| 10D.7 | Add debug logging to job parse results | `frontend/src/components/job-intake/JobIntakeForm.tsx` | ✅ |
| 10D.8 | Fix BBC experience DOCX rendering | `services/docx_resume.py` | ✅ |
| 10D.9 | Fix frontend date formatting (M/YYYY) | `frontend/src/components/generation/ResultsPanel.tsx` | ✅ |
| 10D.10 | Enrich user skill tags from bullet analysis | Database | ✅ |
| 10D.11 | Fix Next.js CSS cache corruption | Frontend | ✅ |

#### Mock Services Audit Results

| Service | Location | Production Ready | Status |
|---------|----------|-----------------|--------|
| `MockLLM` | `services/llm/mock_llm.py` | ⚠️ Real LLM not implemented | Used in all generation |
| `MockEmbeddingService` | `services/embeddings.py` | ✅ `OpenAIEmbeddingService` exists | `use_mock=True` in skill_gap.py |
| `MockVectorStore` | `services/vector_store.py` | ✅ `QdrantVectorStore` exists | Production uses live |
| `MockLLMService` | `services/skill_gap.py` | ⚠️ Real LLM not implemented | Used for skill gap |

**Key Finding:** Only `skill_gap.py:41` has hardcoded `use_mock=True`. All other production code uses live services.

#### Skill Similarity Mappings Added

Added 22 new skill pairs to `MockEmbeddingService`:

**AI-Related:**
- `AI` ↔ `AI Strategy` (0.85)
- `AI` ↔ `AI/ML` (0.92)
- `AI` ↔ `AI Governance` (0.78)
- `AI Strategy` ↔ `Strategy` (0.82)
- `AI/ML` ↔ `Machine Learning` (0.95)
- `Generative AI` ↔ `AI` (0.88)
- `LLM` ↔ `AI` (0.82)

**Consulting-Related:**
- `Digital Transformation` ↔ `Strategy` (0.75)
- `Digital Transformation` ↔ `Change Management` (0.76)
- `Strategy` ↔ `Business Strategy` (0.93)
- `Consulting` ↔ `Technology Consulting` (0.90)
- `Stakeholder Management` ↔ `Client Management` (0.82)

#### Company Name Extraction Improvements

Enhanced `extract_company_name()` with additional patterns:
- `about\s+([Company])(?:\s*:|\s*$)` - "About AHEAD:" format
- `(?:work|working)\s+(?:at|for|with)\s+([Company])` - "work at AHEAD"
- `posted\s+by\s*:?\s*([Company])` - "Posted by Company Name"
- `hiring\s+company\s*:?\s*([Company])` - "Hiring Company: Name"

#### User Profile Enrichment

Added 13 new skill tags to User 1's bullet tags based on content analysis:
- `Consulting` (6 bullets)
- `Strategy` (4 bullets)
- `Stakeholder Management` (1 bullet)
- `Client Engagement` (3 bullets)
- `Digital Transformation` (1 bullet)
- `Machine Learning` (1 bullet)
- `Team Leadership` (6 bullets)
- `Enterprise Strategy` (2 bullets)
- `Systems Integration` (1 bullet)
- `Roadmapping` (1 bullet)
- `Vector Search` (2 bullets)
- `Go-to-Market` (1 bullet)
- `Innovation` (3 bullets)
- `Business Analysis` (1 bullet)

**Result:** User skill tags increased from 74 → 87, skill match score improved from 53.5% → 82.2% for AI Consultant roles.

#### Frontend Fixes

1. **Editable Company Name:** Added pencil icon to edit company name when auto-extraction fails
2. **Date Formatting:** Fixed ISO dates to display as M/YYYY format
3. **Engagement Bullets:** Added `getRoleBullets()` helper to include engagement bullets in display
4. **Debug Logging:** Added console.log for parsed job results
5. **CSS Cache Fix:** Documented `.next` folder deletion to fix corrupted static assets

#### Acceptance Criteria
- [x] Mock services documented with production alternatives
- [x] Skill matching improved for AI/consulting skills
- [x] Company name can be manually edited in frontend
- [x] User skill profile enriched with 13 new tags
- [x] Frontend styling issues resolved

#### Plan for Live Services

**Quick Win (Ready Now):**
- Change `skill_gap.py:41` from `use_mock=True` to `use_mock=False` for real embeddings

**Future Work (New Sprint Required):**
- Implement `ClaudeLLM` class for real LLM calls
- Add API key configuration to `config/config.yaml`
- Update `resume_tailor.py`, `cover_letter.py`, `critic.py` to use real LLM
- Estimated effort: 8-12 hours

---

### Sprint 10E: Interactive Skill Selection Panel ✅ COMPLETE

**Goal:** Replace passive skill gap display with an interactive skill selection UI that gives users control over which skills are used for resume/cover letter generation.

**Problem Statement:** The current semantic skill matching is unreliable. Users see confusing results and have no control over skill prioritization. The proposed solution lets users curate skills themselves while the system provides match scores as guidance.

**Status:** ✅ Complete (Dec 2025)

#### Design Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Skills for This Application                    [Save]      │
├─────────────────────────────────────────────────────────────┤
│  ☐ Key  Skill                           Match   [drag] [×]  │
│  ─────────────────────────────────────────────────────────  │
│  ☑      Data Governance        ████████████████  92%        │
│  ☑      Collibra               ░░░░░░░░░░░░░░░░   0%        │
│  ☐      Stakeholder Mgmt       ████████████░░░░  78%        │
│  ☐      Requirements Analysis  ██████████░░░░░░  65%        │
│  ...                                                        │
│                                                             │
│  ⚠ 2/4 key skills selected (select 3-4 for cover letter)   │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Draggable rows to set priority order (affects bullet selection weight)
- "Key" checkbox (max 3-4) → these become `key_skills` for cover letter focus
- Color-coded match bars: green (70%+), yellow (40-70%), red (<40%)
- Remove button (×) to exclude irrelevant extracted skills
- Persisted per job profile in `selected_skills` and `key_skills` fields

#### Tasks

| ID | Task | File(s) | Priority |
|----|------|---------|----------|
| **Backend** | | | |
| 10E.1 | Add `selected_skills` JSON field to JobProfile model | `db/models.py` | P0 |
| 10E.2 | Add `key_skills` JSON field to JobProfile model | `db/models.py` | P0 |
| 10E.3 | Create `PUT /job-profiles/{id}/skills` endpoint | `routers/job_profile.py` | P0 |
| 10E.4 | Create SkillSelection schema | `schemas/job_profile.py` | P0 |
| 10E.5 | Modify `cover_letter.py` to use `key_skills` for focus | `services/cover_letter.py` | P1 |
| 10E.6 | Modify `resume_tailor.py` to use `selected_skills` for bullet weighting | `services/resume_tailor.py` | P1 |
| 10E.7 | Add skill match % calculation endpoint (or include in parse response) | `services/skill_gap.py` | P1 |
| **Frontend** | | | |
| 10E.8 | Install `@dnd-kit/core` and `@dnd-kit/sortable` | `package.json` | P0 |
| 10E.9 | Create `SkillSelectionPanel` component with drag-drop grid | `components/skills/SkillSelectionPanel.tsx` | P0 |
| 10E.10 | Create `SkillRow` component with checkbox, bar, remove button | `components/skills/SkillRow.tsx` | P0 |
| 10E.11 | Add key skill selection logic (max 3-4 enforcement) | `SkillSelectionPanel.tsx` | P1 |
| 10E.12 | Wire up save button to `PUT /job-profiles/{id}/skills` | `SkillSelectionPanel.tsx` | P0 |
| 10E.13 | Replace `SkillGapPanel` with `SkillSelectionPanel` in main page | `app/page.tsx` | P1 |
| 10E.14 | Add match % display with color-coded progress bars | `SkillRow.tsx` | P1 |
| **Testing** | | | |
| 10E.15 | Add backend tests for skill selection endpoint | `tests/test_skill_selection.py` | P1 |
| 10E.16 | Add integration test: selected skills → resume output | `tests/test_skill_selection.py` | P2 |

#### Data Model Changes

```python
# JobProfile additions
class JobProfile(Base):
    # ... existing fields ...

    # User-curated skill selections (Sprint 10E)
    selected_skills: Mapped[Optional[List[Dict]]] = mapped_column(
        JSON,
        nullable=True,
        comment="User-ordered list of skills: [{skill: str, match_pct: float, included: bool}]"
    )
    key_skills: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="3-4 skills to emphasize in cover letter"
    )
```

#### API Schema

```python
class SkillSelectionUpdate(BaseModel):
    """Request to update skill selections for a job profile."""
    selected_skills: List[SelectedSkill]  # Ordered list
    key_skills: List[str] = Field(max_length=4)  # Max 4 key skills

class SelectedSkill(BaseModel):
    skill: str
    match_pct: float
    included: bool = True  # False if user removed it
```

#### Acceptance Criteria

- [ ] Users can drag-drop to reorder skills
- [ ] Users can check 3-4 "key" skills for cover letter emphasis
- [ ] Users can remove irrelevant skills from the list
- [ ] Match percentages displayed with color-coded bars
- [ ] Selections persisted to database per job profile
- [ ] Cover letter generation uses `key_skills` for paragraph focus
- [ ] Resume bullet selection uses `selected_skills` order for weighting
- [ ] All existing tests continue to pass

#### Estimated Effort

| Component | Hours |
|-----------|-------|
| Backend (10E.1-10E.7) | 4-5h |
| Frontend (10E.8-10E.14) | 8-10h |
| Testing (10E.15-10E.16) | 2-3h |
| **Total** | 14-18h |

#### Dependencies

- Requires: Sprint 10D complete ✅
- Blocks: None (Phase 2 can proceed independently)

---

### Sprint 11: Capability-Aware Skill Extraction 🔄 IN PROGRESS

**Goal:** Replace flat skill extraction with a three-tier capability model that better represents senior/strategic roles. Use LLM to extract capability clusters from JDs, cache mappings to reduce costs, and map resume bullets to clusters they demonstrate.

**Problem Statement:** Current skill extraction uses keyword matching against a 200-skill taxonomy. This is insufficient for senior roles requiring compound capabilities (e.g., "AI Strategy + Stakeholder Management"). Skills are flat tokens without context about seniority, domain, or integration requirements.

**Status:** 🔄 In Progress

#### Three-Tier Capability Model

```
Tier 1: Capability Clusters (4-6 per role)
   ├── AI & Data Strategy
   ├── Solution Architecture
   ├── Client Advisory
   └── Domain Expertise

Tier 2: Component Skills (3-8 per cluster)
   ├── AI Strategy → [roadmap creation, value articulation, adoption guidance]
   ├── Solution Architecture → [data architecture, cloud integration, IoT, digital twins]
   └── ...

Tier 3: Evidence Skills (atomic, matchable)
   ├── TensorFlow, PyTorch, Databricks, AWS, etc.
```

#### Tasks

| ID | Task | File(s) | Priority | Est. |
|----|------|---------|----------|------|
| **Phase 1: Data Model** | | | |
| 11.1 | Create Capability Cluster Pydantic schemas | `schemas/capability.py` | P0 | 2h |
| 11.2 | Add `capability_clusters` JSON field to JobProfile | `db/models.py` | P0 | 1h |
| 11.3 | Create Capability Ontology (20-30 clusters) | `services/capability_ontology.py` | P0 | 4h |
| **Phase 2: LLM Extraction** | | | |
| 11.4 | Implement LLM Cluster Extraction Service | `services/capability_extractor.py` | P0 | 8h |
| 11.5 | Implement Cluster Cache Service | `services/cluster_cache.py` | P0 | 3h |
| **Phase 3: Evidence Mapping** | | | |
| 11.6 | Implement Bullet-to-Cluster Mapper | `services/evidence_mapper.py` | P0 | 6h |
| 11.7 | Integrate Cluster Analysis into Skill Gap Service | `services/skill_gap.py` | P0 | 4h |
| **Phase 4: API** | | | |
| 11.8 | Create Capability Cluster API Endpoints | `routers/capability.py` | P1 | 2h |
| **Phase 5: Frontend** | | | |
| 11.9 | Create CapabilityClusterPanel Component | `components/analysis/CapabilityClusterPanel.tsx` | P0 | 8h |
| 11.10 | Update JobIntakeForm to fetch clusters | `components/job-intake/JobIntakeForm.tsx` | P1 | 2h |
| 11.11 | Update API Client with cluster methods | `lib/api.ts` | P1 | 1h |
| **Phase 6: Integration** | | | |
| 11.12 | Update Resume Tailor to use cluster evidence | `services/resume_tailor.py` | P1 | 3h |
| 11.13 | Update Cover Letter Service to use key skills | `services/cover_letter.py` | P1 | 3h |
| 11.14 | Write Unit Tests (40+ tests) | `tests/test_capability_extraction.py` | P0 | 6h |

#### Data Model Changes

```python
# schemas/capability.py
class EvidenceSkill(BaseModel):
    """Atomic, matchable skill (Tier 3)"""
    name: str
    category: str  # tech, domain, soft_skill
    matched: bool = False

class ComponentSkill(BaseModel):
    """Component skill within cluster (Tier 2)"""
    name: str
    evidence_skills: List[EvidenceSkill] = []
    required: bool = True

class CapabilityCluster(BaseModel):
    """High-level capability cluster (Tier 1)"""
    name: str
    description: str
    component_skills: List[ComponentSkill]
    match_percentage: float = 0.0
    importance: str = "critical"  # critical, important, nice-to-have
    user_evidence: List[str] = []  # bullet IDs
    gaps: List[str] = []  # missing tech within this cluster
    positioning: Optional[str] = None

class CapabilityClusterAnalysis(BaseModel):
    """Full cluster-based skill gap analysis"""
    job_profile_id: int
    clusters: List[CapabilityCluster]
    overall_match_score: float
    recommendation: str
    positioning_summary: str
```

#### UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ Capability Analysis                                    [Save]   │
├─────────────────────────────────────────────────────────────────┤
│ Overall Match: 78% | Recommendation: Strong Match               │
│                                                                 │
│ ▼ AI & Data Strategy (85% match) ─────────────────── Critical  │
│   ☑️ AI/ML Strategy & Roadmaps          ████████████░░ 92%     │
│   ☑️ Data Architecture & Governance     ████████████░░ 88%     │
│   ☐ Value Articulation to Executives   ████████░░░░░░ 65%     │
│                                                                 │
│ ▼ Solution Architecture (72% match) ─────────────── Critical   │
│   ☑️ Cloud Ecosystems (AWS/Azure/GCP)   █████████████░ 90%     │
│   ⚠️ Digital Twins                      ░░░░░░░░░░░░░░  0% GAP │
│   ⚠️ Smart City / Mobility              ░░░░░░░░░░░░░░  0% GAP │
│                                                                 │
│ ▶ Client Advisory (70% match) ──────────────────── Important   │
│ ▶ Technical Depth (88% match) ──────────────────── Important   │
│                                                                 │
│ ─────────────────────────────────────────────────────────────── │
│ ⭐ Key Skills for Cover Letter (select 3-4):                    │
│   ☑️ AI/ML Strategy          ☑️ Cloud Architecture              │
│   ☐ Data Governance          ☐ Technical Leadership            │
│                                                                 │
│ 🎯 Gaps to Address:                                             │
│   • Digital Twins (position as growth area)                     │
│   • Transportation domain (emphasize pattern transfer)          │
└─────────────────────────────────────────────────────────────────┘
```

#### Acceptance Criteria

- [ ] LLM extracts 4-6 capability clusters from JDs
- [ ] Cluster mappings cached with 24-hour TTL (configurable)
- [ ] Resume bullets mapped to clusters with match percentages
- [ ] UI displays hierarchical clusters with tech gaps visible
- [ ] Key skill selection (3-4 max) for cover letter focus
- [ ] Specific tech gaps surfaced within each cluster
- [ ] Backward compatible with existing flat skill extraction
- [ ] MockLLM works for testing (no real API calls in tests)
- [ ] All existing tests continue to pass

#### Estimated Effort

| Phase | Hours |
|-------|-------|
| Phase 1: Data Model (11.1-11.3) | 7h |
| Phase 2: LLM Extraction (11.4-11.5) | 11h |
| Phase 3: Evidence Mapping (11.6-11.7) | 10h |
| Phase 4: API (11.8) | 2h |
| Phase 5: Frontend (11.9-11.11) | 11h |
| Phase 6: Integration (11.12-11.14) | 12h |
| **Total** | **53h** |

#### Dependencies

- Requires: Sprint 10E complete ✅
- Blocks: Phase 2 Company Intelligence (uses capability clusters for company matching)

---

## Phase 2: Company Intelligence

### Sprint 12: Company Profile Enrichment (PRD 5.1-5.2)

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

### Sprint 13: Hiring Manager Inference (PRD 5.3)

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

### Sprint 14: Warm Contact Identification (PRD 5.4)

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

### Sprint 15: Networking Outputs (PRD 5.5-5.6)

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
Sprint 9 (Frontend) → depends on → Sprint 8C (Pagination) ✅
Sprint 10 (UI) → depends on → Sprint 9 (Next.js setup) ✅
Sprint 10B (Extraction Quality) → depends on → Sprint 10 (UI) ✅
Sprint 10D (Debugging) → depends on → Sprint 10B (Extraction) ✅
Phase 2 → depends on → Phase 1E complete (Sprint 10D) ✅
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

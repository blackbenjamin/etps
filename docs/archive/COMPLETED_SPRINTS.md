# ETPS Completed Sprints Archive
**Historical Implementation Details for Sprints 1-12**
**Archived: December 2025**

This document contains detailed task lists, implementation notes, and acceptance criteria for completed sprints. For current project status, see `docs/IMPLEMENTATION_PLAN.md`.

---

## Phase 1A: Core Quality

### Sprint 1: Resume Critic Agent (PRD 4.1-4.5) - Completed Dec 2025

**Goal:** Implement a critic agent that evaluates resume quality against a rubric and triggers revisions.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 1.1.1 | Define ResumeCriticResult schema | `schemas/critic.py` | Done |
| 1.1.2 | Implement resume rubric evaluation | `services/critic.py` | Done |
| 1.1.3 | Add JD alignment scoring | `services/critic.py` | Done |
| 1.1.4 | Add clarity/conciseness scoring | `services/critic.py` | Done |
| 1.1.5 | Add impact orientation scoring | `services/critic.py` | Done |
| 1.1.6 | Add tone validation | `services/critic.py` | Done |
| 1.1.7 | Add formatting fidelity check | `services/critic.py` | Done |
| 1.1.8 | Add hallucination detection | `services/critic.py` | Done |
| 1.1.9 | Implement critic iteration loop | `services/resume_tailor.py` | Done |
| 1.1.10 | Add max iterations config | `config/config.yaml` | Done |
| 1.1.11 | Add critic logging | `services/critic.py` | Done |
| 1.1.12 | Write unit tests | `test_resume_critic.py` | Done |

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

### Sprint 2: Skill-Gap Analysis with Semantic Matching (PRD 1.4, 2.7) - Completed Dec 2025

**Goal:** Implement comprehensive skill-gap analysis with semantic embedding matching.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 2.1 | Define SkillGapResponse schema | `schemas/skill_gap.py` | Done |
| 2.2 | Implement embeddings service | `services/embeddings.py` | Done |
| 2.3 | OpenAI embedding integration | `services/embeddings.py` | Done |
| 2.4 | Semantic skill matching | `services/skill_gap.py` | Done |
| 2.5 | Weak signal detection | `services/skill_gap.py` | Done |
| 2.6 | LLM-based gap categorization | `services/skill_gap.py` | Done |
| 2.7 | Positioning strategy generation | `services/skill_gap.py` | Done |
| 2.8 | Database caching with 24h expiry | `services/skill_gap.py` | Done |
| 2.9 | Thread-safe singleton patterns | `services/skill_gap.py` | Done |
| 2.10 | Write unit tests | `test_skill_gap.py` | Done |

#### Implementation Notes
- `services/embeddings.py` - BaseEmbeddingService, MockEmbeddingService, OpenAIEmbeddingService
- `services/skill_gap.py` - ~1300 lines with full semantic matching
- Similarity threshold tuned to 0.60 for OpenAI text-embedding-3-small
- 24 unit tests passing

---

### Sprint 3: Cover Letter Critic (PRD 3.7, 4.8) - Completed Dec 2025

**Goal:** Implement cover letter critic with iteration loop and LLM-based revision.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 3.1 | Define CriticIssue schema | `schemas/cover_letter.py` | Done |
| 3.2 | Define CoverLetterCriticResult schema | `schemas/cover_letter.py` | Done |
| 3.3 | Add iteration tracking to GeneratedCoverLetter | `schemas/cover_letter.py` | Done |
| 3.4 | Implement evaluate_cover_letter() | `services/cover_letter.py` | Done |
| 3.5 | Implement critic iteration loop | `services/cover_letter.py` | Done |
| 3.6 | Add revise_cover_letter() to LLM interface | `services/llm/base.py` | Done |
| 3.7 | Implement MockLLM revision with phrase replacements | `services/llm/mock_llm.py` | Done |
| 3.8 | Add CriticLog model for persistence | `db/models.py` | Done |
| 3.9 | Write unit tests | `test_cover_letter_critic.py` | Done |

#### Implementation Notes
- Critic iteration loop in `services/cover_letter.py` (lines 1114-1340)
- Quality threshold: 75 points (configurable)
- Max iterations: 3 (configurable)
- MockLLM includes 40+ banned phrase replacements
- 14 unit tests passing

---

## Phase 1B: Schema Migration

### Sprint 4: Schema & Data Migration (v1.3.0) - Completed Dec 2025

**Goal:** Migrate database schema to v1.3.0 with engagement hierarchy and update resume data.

#### Tasks - Database Schema

| ID | Task | Description |
|----|------|-------------|
| 4.1.1 | Add `engagements` table | id, experience_id, client, project_name, project_type, date_range_label, domain_tags, tech_tags, order |
| 4.1.2 | Update `bullets` table | Add engagement_id FK (nullable for non-consulting roles) |
| 4.1.3 | Update `experiences` table | Add employer_type, role_summary, ai_systems_built, governance_frameworks_created, fs_domain_relevance, tools_and_technologies |
| 4.1.4 | Update `users` table | Add primary_identity, specializations, target_roles, ai_systems_builder, portfolio_url, linkedin_meta (JSON) |
| 4.1.5 | Update `skills` table | Add category, level, core fields |
| 4.1.6 | Add education fields | Add prestige_weight, executive_credibility_score, language_fluency |

#### Engagement Structure
```
Benjamin Black Consulting | Boston, MA                    10/2025 - Present
Independent AI Strategist & Builder
  [Role summary bullet]

  Edward Jones - Enterprise Data Strategy & Governance
    - Bullet 1
    - Bullet 2

  Darling Consulting Group - Data Strategy & Analytics Portal
    - Bullet 1
```

---

## Phase 1C: LLM Enhancement

### Sprint 5: Bullet Rewriting & Selection (PRD 2.4, 2.6, 2.8, 2.9, 4.3) - Completed Dec 2025

**Goal:** Implement LLM-powered bullet rewriting, deterministic bullet selection algorithm, engagements nesting, and truthfulness checks.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 1.4.1 | Create bullet rewriting prompt template | `services/llm/prompts/` | Done |
| 1.4.2 | Implement bullet rewriter service | `services/bullet_rewriter.py` | Done |
| 1.4.3 | Add STAR notes integration | `services/bullet_rewriter.py` | Done |
| 1.4.4 | Implement version history storage | `db/models.py` | Done |
| 1.4.5 | Add rewrite validation (no hallucination) | `services/bullet_rewriter.py` | Done |
| 1.4.6 | Track original vs rewritten text | `schemas/resume_tailor.py` | Done |
| 1.4.7 | Add rewrite toggle (enable/disable) | `schemas/resume_tailor.py` | Done |
| 1.4.8 | Integrate with resume tailor flow | `services/resume_tailor.py` | Done |
| 1.4.9 | Write unit tests | `tests/test_bullet_rewriter.py` | Done |
| 1.4.10 | Implement deterministic bullet selection algorithm | `services/resume_tailor.py` | Done |
| 1.4.11 | Integrate portfolio project bullets | `services/resume_tailor.py` | Done |
| 1.4.12 | Nest engagements under consulting experiences | `services/resume_tailor.py` | Done |
| 1.4.13 | Implement resume truthfulness consistency check | `services/resume_critic.py` | Done |

---

### Sprint 5B: Summary Rewrite Engine (PRD 2.10) - Completed Dec 2025

**Goal:** Implement a summary rewriting module that tailors the professional summary to each job.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 5B.1 | Design summary rewrite prompt template | `services/llm/prompts/summary_rewrite.txt` | Done |
| 5B.2 | Implement SummaryRewriteService | `services/summary_rewrite.py` | Done |
| 5B.3 | Integrate with resume_tailor pipeline | `services/resume_tailor.py` | Done |
| 5B.4 | Enforce banned phrases and tone via critic | `services/critic.py` | Done |
| 5B.5 | Add unit tests for summary rewrite | `tests/test_summary_rewrite.py` | Done |

#### Implementation Notes
- `services/summary_rewrite.py` - Core rewrite service (~340 lines)
- Uses `candidate_profile.primary_identity`, `specializations`, and `target_roles`
- 53 unit tests passing

---

### Sprint 6: Version History & Plain Text (PRD 2.5, 2.6) - Completed Dec 2025

**Goal:** Implement bullet version history and text/plain output format.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 1.6.1 | Design version history JSON schema | `db/models.py` | Done |
| 1.6.2 | Implement version tracking on save | `services/bullet_rewriter.py` | Done |
| 1.6.3 | Add version history retrieval API | `routers/resume.py` | Done |
| 1.6.4 | Implement plain text resume generator | `services/text_resume.py` | Done |
| 1.6.5 | Implement plain text cover letter generator | `services/text_cover_letter.py` | Done |
| 1.6.6 | Add output format selection to API | `routers/resume.py`, `routers/cover_letter.py` | Done |
| 1.6.7 | Write unit tests | `tests/test_text_output.py` | Done |
| 1.6.8 | Refine DOCX resume template | `services/docx_resume.py` | Done |

#### Implementation Notes
- `services/text_resume.py` - ATS-friendly plain text (~280 lines)
- `services/text_cover_letter.py` - Business letter format (~145 lines)
- API format parameter: `?format=docx|text|json` with docx as default
- 64 unit tests in test_text_output.py

---

## Phase 1D: Vector Search & Learning

### Sprint 7: Qdrant Integration (PRD 6.3) - Completed Dec 2025

**Goal:** Set up Qdrant vector store for semantic search.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 1.7.1 | Add Qdrant to requirements | `requirements.txt` | Done |
| 1.7.2 | Create Qdrant client wrapper | `services/vector_store.py` | Done |
| 1.7.3 | Define collection schemas | `services/vector_store.py` | Done |
| 1.7.4 | Implement bullet embedding generation | `services/embeddings.py` | Done |
| 1.7.5 | Implement job profile embedding | `services/embeddings.py` | Done |
| 1.7.6 | Create bullet indexing service | `services/vector_store.py` | Done |
| 1.7.7 | Create job similarity search | `services/vector_store.py` | Done |
| 1.7.8 | Add embedding model config | `config/config.yaml` | Done |
| 1.7.9 | Write integration tests | `tests/test_vector_store.py` | Done |

#### Implementation Notes
- `services/vector_store.py` - Complete vector store service (~1000 lines)
- `BaseVectorStore` abstract class with `QdrantVectorStore` and `MockVectorStore` implementations
- Collection schemas: bullets, jobs, approved_outputs
- 54 unit tests passing

---

### Sprint 8: Learning from Approved Outputs (PRD 4.7) - Completed Dec 2025

**Goal:** Store approved outputs and retrieve similar examples for new requests.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 1.8.1 | Create ApprovedOutput model | `db/models.py` | Done |
| 1.8.2 | Implement output approval API | `routers/outputs.py` | Done |
| 1.8.3 | Index approved outputs in Qdrant | `services/vector_store.py` | Done |
| 1.8.4 | Implement similar output retrieval | `services/output_retrieval.py` | Done |
| 1.8.7 | Write unit tests | `tests/test_approved_outputs.py` | Done |

#### Implementation Notes
- 45 unit tests in test_approved_outputs.py
- ApprovedOutput model with user, application, job_profile relationships
- POST /outputs/approve and GET /outputs/similar endpoints

---

### Sprint 8B: Gap Remediation (PRD Integration Gaps) - Completed Dec 2025

**Goal:** Address critical integration gaps identified in post-Sprint 8 review.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 8B.1 | Integrate approved bullets into resume generation | `services/resume_tailor.py` | Done |
| 8B.2 | Integrate approved paragraphs into cover letter generation | `services/cover_letter.py` | Done |
| 8B.3 | Integrate skill gap results into bullet selection | `services/resume_tailor.py` | Done |
| 8B.4 | Implement truthfulness validation in resume critic | `services/critic.py` | Done |
| 8B.5 | Add em-dash detection to resume critic | `services/critic.py` | Done |
| 8B.6 | Add max_iterations to config.yaml | `config/config.yaml` | Done |
| 8B.7 | Pass STAR notes to bullet rewriter | `services/bullet_rewriter.py` | Done |
| 8B.8 | Thread context_notes to summary rewrite | `services/summary_rewrite.py` | Done |
| 8B.9 | Verify portfolio integration end-to-end | `services/resume_tailor.py` | Done |
| 8B.10 | Write integration tests | `tests/test_sprint_8b_integration.py` | Done |

---

### Sprint 8C: Pagination-Aware Layout & Page Budgeting (PRD 2.11) - Completed Dec 2025

**Goal:** Implement pagination-aware resume layout with global space budgeting.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 8C.1 | Add pagination constants to config.yaml | `config/config.yaml` | Done |
| 8C.2 | Implement line budget cost estimator | `services/pagination.py` | Done |
| 8C.3 | Implement value-per-line bullet allocation | `services/pagination.py` | Done |
| 8C.4 | Implement PageSplitSimulator | `services/pagination.py` | Done |
| 8C.5 | Add per-role constraints and condensation | `services/resume_tailor.py` | Done |
| 8C.6 | Implement bullet compression mode | `services/bullet_rewriter.py`, `services/pagination.py` | Done |
| 8C.7 | Add max_lines hint to summary_rewrite | `services/summary_rewrite.py` | Done |
| 8C.8 | Add pagination sanity checks to critic | `services/critic.py` | Done |
| 8C.9 | Add unit tests (44 tests) | `tests/test_pagination_allocation.py` | Done |
| 8C.10 | Add regression tests (42 tests) | `tests/test_sprint_8c_regression.py` | Done |

#### Security Hardening (Post-Review)
- Pre-compiled regex patterns to prevent ReDoS attacks
- Input length validation (500 char max for compression)
- Bounds checking on max_lines parameter (1-100)
- Improved exception handling with specific error types

---

## Phase 1E: Frontend MVP

### Sprint 9-10: Next.js Setup & Job Intake UI (PRD 6.6) - Completed Dec 2025

**Goal:** Set up Next.js frontend with Tailwind, shadcn/ui, and main job intake page.

#### Key Components Built
- `frontend/src/app/layout.tsx` - Base layout
- `frontend/src/lib/api.ts` - API client
- `frontend/src/components/JobIntakeForm.tsx` - JD text/URL input
- `frontend/src/components/GenerateButtons.tsx` - Resume/CL generation
- `frontend/src/components/DownloadButtons.tsx` - DOCX/TXT/JSON downloads
- `frontend/src/components/ResultsPanel.tsx` - Results display
- `frontend/src/components/SkillGapPanel.tsx` - Skill gap analysis

---

### Sprint 10B: JD Extraction Quality & Parser Improvements - Completed Dec 2025

**Goal:** Implement automatic quality validation for URL-based job description extraction.

#### Key Features
- `ExtractionQuality` dataclass with `is_valid`, `score`, `issues`, `suggestions`
- Quality checks: minimum length, job keywords, error indicators, boilerplate ratio
- `SECTION_STOP_PATTERNS` to stop parsing at salary/benefits/EEO sections
- URL normalization for Lever/Greenhouse
- Frontend amber warning for extraction failures

---

### Sprint 10C: Parser & Skill Gap Fixes - Completed Dec 2025

**Goal:** Fix company/title/location extraction and skill gap score calculation.

---

### Sprint 10D: Debugging & Improvements - Completed Dec 2025

**Goal:** Address various debugging issues, audit mock services, improve skill matching.

#### Mock Services Audit Results

| Service | Production Ready | Status |
|---------|-----------------|--------|
| `MockLLM` | Real LLM not implemented | Used in all generation |
| `MockEmbeddingService` | `OpenAIEmbeddingService` exists | `use_mock=True` in skill_gap.py |
| `MockVectorStore` | `QdrantVectorStore` exists | Production uses live |

#### Skill Similarity Mappings Added
- 22 new AI/consulting skill pairs in `MockEmbeddingService`
- User skill tags increased from 74 to 87
- Skill match score improved from 53.5% to 82.2%

---

### Sprint 10E: Interactive Skill Selection Panel - Completed Dec 2025

**Goal:** Replace passive skill gap display with interactive skill selection UI.

#### Key Features
- Draggable rows to set priority order
- "Key" checkbox (max 3-4) for cover letter focus
- Color-coded match bars: green (70%+), yellow (40-70%), red (<40%)
- Remove button to exclude irrelevant extracted skills
- Persisted per job profile in `selected_skills` and `key_skills` fields

---

## Phase 1F: Capability Extraction

### Sprint 11: Capability-Aware Skill Extraction - Completed Dec 2025

**Goal:** Replace flat skill extraction with a three-tier capability model.

#### Three-Tier Model
```
Tier 1: Capability Clusters (4-6 per role)
   - AI & Data Strategy
   - Solution Architecture
   - Client Advisory
   - Domain Expertise

Tier 2: Component Skills (3-8 per cluster)
   - AI Strategy -> [roadmap creation, value articulation, adoption guidance]
   - Solution Architecture -> [data architecture, cloud integration, IoT]

Tier 3: Evidence Skills (atomic, matchable)
   - TensorFlow, PyTorch, Databricks, AWS, etc.
```

#### Implementation Notes
- `services/capability_ontology.py` - 20-30 predefined clusters
- `services/capability_extractor.py` - LLM-based extraction
- `services/evidence_mapper.py` - Bullet-to-cluster mapping
- 37 unit tests passing

---

### Sprint 11B: LLM Anti-Hallucination - Completed Dec 2025

**Goal:** Prevent LLM from injecting skills not present in the job description.

#### Fixes Implemented
- Neutralized reference summary (removed AI bias)
- Added anti-hallucination rules to summary prompt
- Removed AI bias from cover letter system prompt
- Added "CRITICAL ANTI-HALLUCINATION RULES" header

---

### Sprint 11C: Hybrid Skill Extraction - Completed Dec 2025

**Goal:** Combine taxonomy-based and LLM-based skill extraction.

#### Features
- Expanded skills taxonomy
- LLM extraction for domain inference
- Resume skills enrichment from bullet analysis

---

### Sprint 11D: Report Unregistered Skills - Completed Dec 2025

**Goal:** Allow users to add skills they possess that aren't currently matched.

#### UX Flow
1. User clicks "I have this" on unmatched skill
2. Modal opens: "Where did you use {skill}?"
3. User selects experience(s), optionally drills down to engagements/bullets
4. User clicks "Confirm" - Skill saved immediately
5. Counter updates: "1 skill added"
6. "Re-run Analysis" button appears
7. User clicks "Re-run Analysis" - Single analysis call

#### API Endpoints
- POST /api/v1/capability/job-profiles/{id}/user-skills
- GET /api/v1/users/{id}/experiences

---

## Phase 2: Company Intelligence

### Sprint 12: Company Profile Enrichment (PRD 5.1-5.2) - Completed Dec 2025

**Goal:** Enrich company profiles with web data and intelligence.

#### Tasks

| ID | Task | File(s) | Status |
|----|------|---------|--------|
| 2.1.1 | Create company enrichment service | `services/company_enrichment.py` | Done |
| 2.1.2 | Extract company from JD | `services/company_enrichment.py` | Done |
| 2.1.3 | Fetch company website data (SSRF protected) | `services/company_enrichment.py` | Done |
| 2.1.4 | Extract industry, size, HQ | `services/company_enrichment.py` | Done |
| 2.1.5 | Infer culture signals | `services/company_enrichment.py` | Done |
| 2.1.6 | Infer data/AI maturity | `services/company_enrichment.py` | Done |
| 2.1.7 | Store enriched profile with deduplication | `db/models.py` | Done |
| 2.1.8 | Add company profile API | `routers/company.py` | Done |
| 2.1.9 | Write unit tests (71 tests) | `tests/test_company_enrichment.py` | Done |

#### Security Features
- SSRF protection (private IP detection, URL validation)
- ReDoS prevention (500-char input limit)
- About-page URL validation before fetching
- Scalable deduplication using ILIKE queries

#### API Endpoints
- POST /api/v1/company/enrich
- GET /api/v1/company/{id}
- GET /api/v1/company/search/
- PUT /api/v1/company/{id}
- DELETE /api/v1/company/{id}

---

*Archived December 2025*

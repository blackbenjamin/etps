# ETPS Implementation Plan
**Full PRD Implementation Roadmap**
**Version 1.0 — December 2025**

---

## Executive Summary

This document provides a detailed implementation plan to build ETPS to full PRD specification. The plan is organized into sprints with specific tasks, acceptance criteria, and dependencies.

**Current State:** Backend foundation with v1.3.0 schema, basic resume/cover letter generation, DOCX formatting.

**Target State:** Full Phase 1 (Core Quality), Phase 2 (Company Intelligence), and Phase 3 (Application Tracking) as defined in ETPS_PRD.md.

---

## Implementation Phases Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1A: Core Quality (Sprints 1-2)                           │
│ - Resume Critic Agent                                           │
│ - ATS Scoring                                                   │
│ - Style Enforcement                                             │
│ - Skill-Gap Analysis                                            │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1B: LLM Enhancement (Sprints 3-4)                        │
│ - Bullet Rewriting                                              │
│ - Cover Letter Critic                                           │
│ - Version History                                               │
│ - Text/Plain Output                                             │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1C: Vector Search & Learning (Sprints 5-6)               │
│ - Qdrant Integration                                            │
│ - Semantic Bullet Matching                                      │
│ - Learning from Approved Outputs                                │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1D: Frontend MVP (Sprints 7-8)                           │
│ - Next.js Setup                                                 │
│ - Job Intake Page                                               │
│ - Generate & Download Workflow                                  │
│ - Skill-Gap Display                                             │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 2: Company Intelligence (Sprints 9-12)                   │
│ - Company Profile Enrichment                                    │
│ - Hiring Manager Inference                                      │
│ - Warm Contact Identification                                   │
│ - Networking Output Generation                                  │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 3: Application Tracking (Sprints 13-15)                  │
│ - Application Status Tracking                                   │
│ - Contact Management                                            │
│ - Reminders & Tasks                                             │
│ - Deployment (Railway + Vercel)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1A: Core Quality

### Sprint 1: Resume Critic Agent (PRD 4.1-4.5)

**Goal:** Implement a critic agent that evaluates resume quality against a rubric and triggers revisions.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.1.1 | Define ResumeCriticResult schema | `schemas/critic.py` | 4.3 | P0 |
| 1.1.2 | Implement resume rubric evaluation | `services/resume_critic.py` | 4.3 | P0 |
| 1.1.3 | Add JD alignment scoring | `services/resume_critic.py` | 4.3 | P0 |
| 1.1.4 | Add clarity/conciseness scoring | `services/resume_critic.py` | 4.3 | P0 |
| 1.1.5 | Add impact orientation scoring | `services/resume_critic.py` | 4.3 | P0 |
| 1.1.6 | Add tone validation | `services/resume_critic.py` | 4.3 | P0 |
| 1.1.7 | Add formatting fidelity check | `services/resume_critic.py` | 4.3 | P1 |
| 1.1.8 | Add hallucination detection | `services/resume_critic.py` | 4.3 | P0 |
| 1.1.9 | Implement critic iteration loop | `services/resume_tailor.py` | 4.4 | P0 |
| 1.1.10 | Add max iterations config | `config/config.yaml` | 4.4 | P1 |
| 1.1.11 | Add critic logging | `services/resume_critic.py` | 4.6 | P1 |
| 1.1.12 | Write unit tests | `tests/test_resume_critic.py` | - | P1 |

#### Acceptance Criteria
- [ ] Critic evaluates resume against all rubric categories
- [ ] Critic returns structured scores (0-100) for each category
- [ ] Critic identifies specific issues with actionable feedback
- [ ] Iteration loop retries up to 3 times on failure
- [ ] All critic decisions logged to database

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

### Sprint 2: ATS Scoring & Style Enforcement (PRD 4.2, 4.8)

**Goal:** Implement ATS keyword scoring and strict style enforcement.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.2.1 | Implement ATS keyword extraction from JD | `services/ats_scorer.py` | 4.2 | P0 |
| 1.2.2 | Calculate keyword density score | `services/ats_scorer.py` | 4.2 | P0 |
| 1.2.3 | Track missing critical keywords | `services/ats_scorer.py` | 4.2 | P0 |
| 1.2.4 | Implement banned phrase detection | `services/style_enforcer.py` | 4.8 | P0 |
| 1.2.5 | Implement em-dash detection | `services/style_enforcer.py` | 4.8 | P0 |
| 1.2.6 | Add weak verb detection | `services/style_enforcer.py` | 4.8 | P1 |
| 1.2.7 | Add sentence length validation | `services/style_enforcer.py` | 4.8 | P1 |
| 1.2.8 | Add passive voice detection | `services/style_enforcer.py` | 4.8 | P2 |
| 1.2.9 | Integrate ATS score into TailoredResume | `schemas/resume_tailor.py` | 4.2 | P0 |
| 1.2.10 | Add configurable ATS threshold | `config/config.yaml` | 4.4 | P1 |
| 1.2.11 | Write unit tests | `tests/test_ats_scorer.py` | - | P1 |

#### Acceptance Criteria
- [ ] ATS score calculated for every generated resume
- [ ] Missing keywords identified and reported
- [ ] Banned phrases cause automatic rejection
- [ ] Em-dashes cause automatic rejection
- [ ] Style scores computed: tone, lexical, conciseness

#### Config: ATS Settings
```yaml
ats:
  score_threshold: 75
  critical_keyword_weight: 2.0
  nice_to_have_weight: 1.0

style:
  banned_phrases:
    - "I am writing to express my interest"
    - "Passionate"
    - "Dynamic professional"
    # ... (full list from PRD 3.5)
  max_sentence_length: 35
  target_sentence_length: [14, 22]
```

---

### Sprint 3: Skill-Gap Analysis (PRD 1.4, 2.7)

**Goal:** Implement comprehensive skill-gap analysis comparing JD requirements to user skills.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.3.1 | Define SkillGapAnalysis schema | `schemas/skill_gap.py` | 2.7 | P0 |
| 1.3.2 | Extract required skills from JD | `services/skill_gap.py` | 2.7 | P0 |
| 1.3.3 | Categorize must-have vs nice-to-have | `services/skill_gap.py` | 2.7 | P0 |
| 1.3.4 | Match user skills to JD requirements | `services/skill_gap.py` | 2.7 | P0 |
| 1.3.5 | Identify skill gaps | `services/skill_gap.py` | 2.7 | P0 |
| 1.3.6 | Generate positioning strategies | `services/skill_gap.py` | 2.7 | P1 |
| 1.3.7 | Calculate overall fit score | `services/skill_gap.py` | 2.7 | P0 |
| 1.3.8 | Integrate into JobProfile model | `db/models.py` | 2.7 | P0 |
| 1.3.9 | Add skill-gap to tailor response | `schemas/resume_tailor.py` | 2.7 | P0 |
| 1.3.10 | Write unit tests | `tests/test_skill_gap.py` | - | P1 |

#### Acceptance Criteria
- [ ] All JD skills extracted and categorized
- [ ] User skills matched with confidence scores
- [ ] Gaps clearly identified with severity
- [ ] Positioning strategies suggested for gaps
- [ ] Overall fit score calculated

#### Schema: SkillGapAnalysis
```python
class SkillGapAnalysis(BaseModel):
    matched_skills: List[MatchedSkill]  # [{skill, confidence, evidence}]
    missing_skills: List[MissingSkill]  # [{skill, importance, suggestion}]
    transferable_skills: List[TransferableSkill]
    overall_fit_score: float  # 0-100
    positioning_strategies: List[str]
    recommended_emphasis: List[str]  # Skills to highlight
```

---

## Phase 1B: LLM Enhancement

### Sprint 4: Bullet Rewriting (PRD 2.4, 2.6)

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

### Sprint 5: Cover Letter Critic (PRD 3.7, 4.8)

**Goal:** Implement cover letter critic with full rubric evaluation.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 1.5.1 | Define CoverLetterCriticResult schema | `schemas/critic.py` | 4.3 | P0 |
| 1.5.2 | Implement structure validation | `services/cover_letter_critic.py` | 4.8 | P0 |
| 1.5.3 | Add tone scoring | `services/cover_letter_critic.py` | 4.8 | P0 |
| 1.5.4 | Add JD requirement alignment check | `services/cover_letter_critic.py` | 4.3 | P0 |
| 1.5.5 | Add company mission integration check | `services/cover_letter_critic.py` | 4.3 | P1 |
| 1.5.6 | Add banned phrase detection | `services/cover_letter_critic.py` | 4.8 | P0 |
| 1.5.7 | Add user instructions verification | `services/cover_letter_critic.py` | 3.2 | P1 |
| 1.5.8 | Implement critic iteration loop | `services/cover_letter.py` | 3.7 | P0 |
| 1.5.9 | Add cover letter logging | `services/cover_letter_critic.py` | 4.6 | P1 |
| 1.5.10 | Write unit tests | `tests/test_cl_critic.py` | - | P1 |

#### Acceptance Criteria
- [ ] Cover letter evaluated against all rubric categories
- [ ] Structure validated (intro → value → requirements → close)
- [ ] Top 2-3 JD requirements explicitly addressed
- [ ] Banned phrases cause automatic rejection
- [ ] Score below 85 triggers regeneration

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

## Phase 1C: Vector Search & Learning

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

## Phase 1D: Frontend MVP

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

### Sprint 17: Deployment (PRD 6.5)

**Goal:** Deploy to Railway (backend) and Vercel (frontend).

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 3.3.1 | Create Railway project | - | 6.5 | P0 |
| 3.3.2 | Configure backend deployment | `railway.toml` | 6.5 | P0 |
| 3.3.3 | Set up environment variables | Railway dashboard | 6.9 | P0 |
| 3.3.4 | Configure Qdrant for production | - | 6.5 | P1 |
| 3.3.5 | Create Vercel project | - | 6.5 | P0 |
| 3.3.6 | Configure frontend deployment | `vercel.json` | 6.5 | P0 |
| 3.3.7 | Set up custom domain | Vercel/Railway | 6.5 | P2 |
| 3.3.8 | Configure CORS for production | `backend/main.py` | 6.5 | P0 |
| 3.3.9 | Add health check endpoints | `backend/routers/health.py` | 6.8 | P1 |
| 3.3.10 | Write deployment documentation | `docs/DEPLOYMENT.md` | - | P1 |

---

## Dependencies & Prerequisites

### External Dependencies
- **Anthropic API Key** - For Claude LLM calls
- **OpenAI API Key** - For embeddings (or alternative)
- **Qdrant** - Local instance for development, cloud for production

### Internal Dependencies
```
Sprint 2 (ATS) → depends on → Sprint 1 (Critic)
Sprint 4 (Rewriting) → depends on → Sprint 1 (Critic)
Sprint 5 (CL Critic) → depends on → Sprint 1 (Critic)
Sprint 8 (Learning) → depends on → Sprint 7 (Qdrant)
Sprint 10 (UI) → depends on → Sprint 9 (Next.js setup)
Phase 2 → depends on → Phase 1A complete
Phase 3 → depends on → Phase 1D complete
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
recruitbot/
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

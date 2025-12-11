# ETPS – PRD & Implementation Plan Amendments
**Addressing Gaps 1–12 Identified in December 2025 Review**  
Target Sprints: **5–10** (Sprints 1–4 already complete)

This document describes specific changes Claude Code should make to:

- `ETPS_PRD.md`
- `IMPLEMENTATION_PLAN.md` (ETPS Implementation Plan)

to close gaps 1–12 identified in the system review.  
All changes are additive or clarifying; they **must not** break existing implemented work (Sprints 1–4).

---

## 0. High-Level Instructions to Claude

1. Treat this file as a **patch spec** for:
   - `ETPS_PRD.md`
   - `docs/IMPLEMENTATION_PLAN.md` (or equivalent)
2. Do **not** re-architect the system; only:
   - Add missing sections
   - Add clarifying text
   - Adjust Sprints 5–10 where indicated
3. Sprints 1–4 are already completed and should be considered **frozen** except for doc updates.
4. All new work should be scheduled into **Sprints 5–10**.

---

## 1) Add Authoritative Runtime Pipeline (Gap #1)

### 1.1 PRD Change

**File:** `ETPS_PRD.md`  
**Location:** After Section `1.3 System Behavior` (or before Section 1.4)

**Add new section:**

```markdown
### 1.6 End-to-End Runtime Pipeline (Authoritative Flow)

For a single job application, ETPS must follow this pipeline:

1. **Job Intake**
   - User provides: JD text and/or URL, optional context notes.
   - System fetches JD text when URL is provided (with SSRF-safe fetch).

2. **JD Parsing → job_profile**
   - Extract title, location, seniority, responsibilities, requirements, skills.
   - Distill 2–3 core priorities for the role.
   - Classify must-have vs nice-to-have capabilities.
   - Store as `job_profile`.

3. **Company Enrichment → company_profile** (Phase 2)
   - Infer company attributes: industry, size, culture signals, AI maturity.
   - Store as `company_profile`.
   - Link `job_profile` ↔ `company_profile`.

4. **Fit & Skill-Gap Analysis**
   - Compare `candidate_profile` + resume schema vs `job_profile`.
   - Compute `match_result` (overall, skills, domain, seniority scores).
   - Compute `SkillGapResponse` with gaps and positioning strategies.

5. **Bullet & Content Selection**
   - Select relevant experiences, engagements, and bullets from:
     - `employment_history.engagements.bullets`
     - `ai_portfolio` (when relevant)
   - Apply the Bullet Selection Algorithm (see Section 2.8).

6. **Summary Rewrite**
   - Rewrite the professional summary using:
     - `candidate_profile`
     - `job_profile.core_priorities`
     - `company_profile` (when available)
   - Enforce summary tone, banned phrases, and length constraints.

7. **Resume Construction (Content)**
   - Assemble selected summary, experiences, skills, and education into a structured JSON representation for this job.
   - Apply any optional LLM bullet rewrites (if enabled).

8. **Cover Letter Generation**
   - Generate a cover letter using:
     - `job_profile`
     - `company_profile`
     - Selected experiences and projects
     - User context notes and style preset
   - Enforce structural requirements (intro → value → alignment → close).

9. **Critic & Refinement Loop**
   - Run Resume Critic on the resume JSON + docx.
   - Run Cover Letter Critic on the cover letter JSON + docx.
   - If failures (style, ATS score, banned phrases, formatting, truthfulness):
     - Regenerate/repair up to max iterations (default 3).
     - Stop when all critical checks pass.

10. **Rendering & Output**
    - Render resume and cover letter to:
      - `.docx` (primary)
      - `text/plain`
      - `application/json`
    - Expose outputs for download and display ATS/skill-gap results.

This pipeline is the authoritative execution order for ETPS and should be reflected in the implementation plan and orchestration code.
```

### 1.2 Implementation Plan Change

**File:** `docs/IMPLEMENTATION_PLAN.md`

**Change:**

- Add a short "Runtime Pipeline" reference near the top, linking back to this new PRD section (no new sprint needed).
- All Sprints 5–10 should assume this pipeline as given.

---

## 2) Bullet Selection Algorithm (Gap #2)

### 2.1 PRD Change

**File:** `ETPS_PRD.md`
**Location:** End of Section 2.6 Bullet & Experience Metadata

**Add new subsection:**

```markdown
### 2.8 Bullet Selection Algorithm

The resume generator must use a deterministic core algorithm for bullet selection, optionally enhanced by LLM heuristics.

**Inputs:**
- `job_profile` (title, core requirements, skills, domain tags)
- `candidate_profile`
- `employment_history[*].engagements[*].bullets`
- `ai_portfolio` (project bullets)
- `domain_tags_master`

**Core Rules:**

1. **Relevance scoring**
   - Compute a relevance score for each bullet based on:
     - Tag overlap (`domain_tags`, `tech_tags` vs job domain/skills).
     - Role type and seniority match.
     - `importance` flag, when present.
   - Optionally use embeddings for semantic similarity.

2. **Per-role bullet count**
   - Default target: 3–6 bullets per major role.
   - Higher seniority roles appear earlier and may receive more bullets.
   - Lower-relevance roles may be shown with fewer bullets.

3. **Engagement prioritization (consulting roles)**
   - For consulting employers, select the 1–3 most relevant engagements for the job.
   - Within each engagement, select the top bullets by relevance score.
   - Less relevant engagements may be omitted from the tailored resume.

4. **Non-consulting roles**
   - For direct employment roles, treat bullets as belonging to the employer, not nested under engagements.
   - Still apply relevance scoring and reordering by relevance.

5. **AI portfolio integration**
   - When the JD is AI/LLM-heavy, allow bullets derived from `ai_portfolio` (e.g., ETPS, RAG systems) to be selected and placed in:
     - The current BBC role, or
     - A Projects/Selected Work section (if present in the template).

6. **Redundancy control**
   - Avoid selecting bullets that repeat the same achievement across roles.
   - Prefer a single strong bullet that represents a theme.

7. **Truthfulness constraints**
   - Never select or generate bullets that invent new employers, roles, or time periods.
   - Only use bullets grounded in existing entries or portfolio projects.

The LLM may assist in ranking or clustering bullets, but the system must follow these deterministic rules for selection and ordering.
```

### 2.2 Implementation Plan Change

**File:** `docs/IMPLEMENTATION_PLAN.md`
**Sprints Affected:** Sprint 5 (Bullet Rewriting) and Sprint 5–6 resume tailoring work

**Add tasks under Sprint 5:**

```markdown
| 1.4.10 | Implement deterministic bullet selection algorithm | `services/resume_tailor.py` | PRD 2.8 | P0 |
| 1.4.11 | Integrate portfolio project bullets when JD is AI/LLM-heavy | `services/resume_tailor.py` | PRD 2.8 | P1 |
```

**Update Sprint 5 Acceptance Criteria:**

```markdown
- [ ] Bullet selection follows PRD 2.8 algorithm (tags + importance + role relevance)
- [ ] Consulting engagements limited to most relevant clients per job
- [ ] Redundant bullets minimized across roles
```

---

## 3) Engagements Representation Consistency (Gap #3)

You already created an engagements table in Sprint 4. We now need to explicitly connect this to the JSON/API and PRD.

### 3.1 PRD Change

**File:** `ETPS_PRD.md`
**Location:** In Section 2 (Resume Data Model), after 2.7

**Add:**

```markdown
### 2.9 Engagements Representation (DB + JSON)

For consulting roles (e.g., Benjamin Black Consulting, Knowledgent), an experience may contain multiple client engagements.

**Database Level:**
- `experiences` table: one row per employer + role + date range.
- `engagements` table: one row per client/project:
  - Foreign key to `experiences`.
  - Fields: client, project_name, project_type, date_range_label, domain_tags, tech_tags, display_order.
- `bullets` table: may belong to:
  - An `experience` directly (non-consulting roles).
  - An `engagement` (consulting/client work).

**API / JSON Level:**
- Resume-tailor API must return a nested structure:
  - `experience` objects containing an `engagements` array.
  - Each engagement contains its `bullets` array.
- For non-consulting roles, `engagements` may be empty and bullets attached directly to the experience.

Rendering and bullet selection must treat engagements as **first-class**, nested under consulting employers.
```

### 3.2 Implementation Plan Change

**File:** `docs/IMPLEMENTATION_PLAN.md`
**Sprints Affected:** Sprint 5–6

**Add to Sprint 5:**

```markdown
| 1.4.12 | Ensure resume_tailor JSON output nests engagements under consulting experiences | `services/resume_tailor.py`, `schemas/resume_tailor.py` | PRD 2.9 | P0 |
```

---

## 4) Summary Rewrite Engine (Gap #4)

### 4.1 PRD Clarification

PRD already implies summary tailoring; we now make it explicit.

**File:** `ETPS_PRD.md`
**Location:** Section 2 (Resume), after 2.9

**Add:**

```markdown
### 2.10 Summary Rewrite Engine

For each job, ETPS must rewrite the professional summary using:

- `candidate_profile` (identity, specializations, target roles)
- `job_profile.core_priorities`
- `company_profile` (mission, industry, AI maturity) when available

Constraints:
- Respect summary tone and banned phrases (Section 4.8).
- Keep within configured word limit (default ≤ 60 words).
- Maintain truthfulness (no added roles or fake responsibilities).
- Emphasize themes aligned to top 2–3 JD priorities.
```

### 4.2 Implementation Plan – New Sprint 5B

**File:** `docs/IMPLEMENTATION_PLAN.md`

Add a new sprint after Sprint 5, positioned between Sprint 5 and Sprint 6.

**Title:** Sprint 5B: Summary Rewrite Engine

```markdown
### Sprint 5B: Summary Rewrite Engine (PRD 2.10)

**Goal:** Implement a summary rewriting module that tailors the professional summary to each job while enforcing tone and banned phrase rules.

#### Tasks

| ID | Task | File(s) | PRD Ref | Priority |
|----|------|---------|---------|----------|
| 5B.1 | Design summary rewrite prompt template | `services/llm/prompts/summary_rewrite.txt` | 2.10 | P0 |
| 5B.2 | Implement SummaryRewriteService | `services/summary_rewrite.py` | 2.10 | P0 |
| 5B.3 | Integrate with resume_tailor pipeline | `services/resume_tailor.py` | 1.6, 2.10 | P0 |
| 5B.4 | Enforce banned phrases and tone via critic | `services/resume_critic.py` | 4.8 | P1 |
| 5B.5 | Add unit tests for summary rewrite | `tests/test_summary_rewrite.py` | 2.10 | P1 |

#### Acceptance Criteria
- [ ] Summary rewritten per job using job_profile core priorities.
- [ ] Summary respects word limit and banned phrases.
- [ ] Critic fails outputs with stale or non-tailored summaries.
```

---

## 5) Company Intelligence → Resume & CL Influence (Gap #5)

### 5.1 PRD Change

**File:** `ETPS_PRD.md`
**Location:** End of Section 5

**Add:**

```markdown
### 5.10 Influence of Company Intelligence on Resume & Cover Letter

When a `company_profile` is available, ETPS must use it to:

1. **Resume:**
   - Select and order bullets that align with:
     - The company's industry.
     - Data/AI maturity level.
     - Mentioned transformations or initiatives.
   - Tilt emphasis toward relevant domains (e.g., banking, broker-dealer, defense).

2. **Summary:**
   - Slightly adjust emphasis (e.g., more AI governance vs more product/engineering) based on company maturity and mission.

3. **Cover Letter:**
   - Connect at least one paragraph to:
     - The company's business lines or products.
     - Problems implied by their maturity level (e.g., need for governance vs experimentation).
   - Adjust tone where culture signals suggest more formal vs more innovative messaging.

The system must not fabricate specific internal initiatives or confidential-sounding strategies; any company-specific claims must be grounded in public information or user-provided context.
```

### 5.2 Implementation Plan Change

**Add to Phase 2 Sprints (11–14):**

- **Sprint 11 (Company Profile Enrichment):** Ensure outputs include `ai_maturity` and `culture_signals`.
- **Sprint 14 (Networking Outputs):** Note that `company_profile` also influences resume and cover letter selection/phrasing.

---

## 6) Clarify Application Tracking Deferral (Gap #6)

### 6.1 PRD Change

**File:** `ETPS_PRD.md`
**Location:** Section 5.8

**Add note:**

```markdown
**Note:** Application tracking, contact history, and reminder workflows are **Phase 3 features**. Phase 1 will only log generation events and critic results; no full tracking UI or workflows are required until Phase 3.
```

No Implementation Plan changes needed (it already places tracking in Phase 3).

---

## 7) Critic Style Rules Codification (Gap #7)

The PRD already defines many rules, but we want them explicitly marked as requirements for the critic.

### 7.1 PRD Change

**File:** `ETPS_PRD.md`
**Location:** Under Section 4.8 Style Enforcement

**Add at the end:**

```markdown
The Critic Agent must treat all style constraints in this section as hard requirements:

- Any banned phrase, em-dash, or structural omission (missing alignment section, missing mission/industry tie-in) constitutes a **critical failure**.
- Critical failures require regeneration or repair until resolved or max iterations reached.
```

### 7.2 Implementation Plan Change

Add to existing Critic sprints (already complete in code but not in docs):

Just update docs to explicitly note that these style rules are enforced as hard constraints (no new code tasks required if this behavior is largely implemented).

---

## 8) Resume Sanity / Truthfulness Checks (Gap #8)

### 8.1 PRD Clarification

**File:** `ETPS_PRD.md`
**Location:** Section 4.3 or 4.5

**Add:**

```markdown
The Critic must validate the following truthfulness constraints for resumes:

- Employer names and job titles must exactly match stored `employment_history` records.
- Employment dates must exactly match stored date ranges.
- Locations must not be altered.
- No new employers, roles, or degrees may appear that do not exist in the underlying data model.

Any violation is a critical failure and must trigger regeneration or a warning that the request cannot be fulfilled as written.
```

### 8.2 Implementation Plan Change

**File:** `docs/IMPLEMENTATION_PLAN.md`
**Sprint Affected:** Sprint 5 (add truthfulness check task)

**Add note in the acceptance criteria or implementation notes:**

```markdown
- Resume Critic validates factual consistency (employers, titles, dates, locations) against stored employment_history data.
```

**Add task to Sprint 5:**

```markdown
| 1.4.13 | Implement resume truthfulness consistency check | `services/resume_critic.py` | PRD 4.3 | P0 |
```

---

## 9) Context Notes Integration (Gap #9)

### 9.1 PRD Change

**File:** `ETPS_PRD.md`
**Location:** Section 1.3 System Behavior or Section 6.6 UI/UX

**Add:**

```markdown
The job intake UI and backend must support an optional free-text "context notes" field. These notes are passed to:

- Summary Rewrite Engine
- Resume bullet selection (for special emphasis or exclusions)
- Cover Letter Generator
- Networking/Outreach Generator (when implemented)

Context notes may include things like:
- "Mention that I spoke with John Smith at the XYZ conference."
- "Do not lean heavily on defense work for this company."
```

### 9.2 Implementation Plan Change

**File:** `docs/IMPLEMENTATION_PLAN.md`
**Sprint Affected:** Sprint 10 (Job Intake & Generation UI)

**Update Sprint 10 tasks:**

1.10.3 already mentions context notes; ensure backend integration is explicit:

```markdown
| 1.10.11 | Pass context notes from UI to backend generation endpoints | `frontend/src/app/page.tsx`, `backend/routers/resume.py`, `backend/routers/cover_letter.py` | PRD 1.6, 6.6 | P0 |
```

---

## 10) ATS Display Clarification (Gap #10)

### 10.1 PRD Enhancement

**File:** `ETPS_PRD.md`
**Location:** Section 1.4 (Success Metrics) or 6.6 (UI/UX)

**Add:**

```markdown
The UI must display ATS-related feedback as:

- A numeric ATS score (0–100).
- A color-coded indicator (e.g., red < 60, yellow 60–75, green > 75).
- A short explanation of which areas are limiting ATS performance (e.g., missing key skills, low keyword overlap in summary).
```

### 10.2 Implementation Plan Change

**File:** `docs/IMPLEMENTATION_PLAN.md`
**Sprint Affected:** Sprint 10

**Update ATS Score Card task:**

```markdown
| 1.10.9 | Add ATS score display with color coding and brief explanation | `frontend/src/components/ATSScoreCard.tsx` | PRD 1.4, 4.3 | P1 |
```

---

## 11) Docx Template Updates After Schema Migration (Gap #11)

Sprint 4 is complete; this is now a post-migration formatting refinement, not part of the migration itself.

### 11.1 PRD Note

No change required; PRD already defines formatting constraints.

### 11.2 Implementation Plan Change

**File:** `docs/IMPLEMENTATION_PLAN.md`
**Sprint Affected:** Sprint 6

**Add a formatting refinement task:**

```markdown
| 1.6.8 | Refine DOCX resume template to match updated header, summary, and skills layout (font sizes, spacing, portfolio line) | `services/docx_resume.py`, `.docx template file` | PRD 2.3, 2.5, header constraints | P0 |
```

**Acceptance Criteria:**

- Header shows name, contact line, and portfolio line as defined.
- Skills section appears in the correct template position and format.
- No unexpected line breaks or misaligned bullets after migration.

---

## 12) Networking Safety Guardrails (Gap #12)

### 12.1 PRD Reinforcement

PRD already mentions risk controls; we make them more explicit for the networking module.

**File:** `ETPS_PRD.md`
**Location:** Section 5.9 Risk Controls

**Add:**

```markdown
Networking and outreach generation must:

- Avoid recommending outreach to C-level executives unless the role is clearly senior enough and the user explicitly opts in.
- Label any inferred org structure or reporting lines with confidence levels.
- Avoid specific claims about internal strategies, restructurings, or confidential initiatives unless they are directly grounded in user-provided context.
```

### 12.2 Implementation Plan Change

**File:** `docs/IMPLEMENTATION_PLAN.md`
**Sprint Affected:** Sprint 14 (Networking Outputs)

**Add:**

```markdown
| 2.4.11 | Implement safety guardrails for outreach suggestions (avoid overreaching senior contacts, label low-confidence inferences) | `services/networking.py`, `services/outreach.py` | PRD 5.9 | P0 |
```

---

## Summary

The changes above:

1. Add a clear runtime pipeline.
2. Specify a bullet selection algorithm.
3. Clarify engagements across DB/JSON.
4. Introduce a dedicated Summary Rewrite Engine.
5. Tie company intelligence into resume and CL generation.
6. Clarify application tracking is Phase 3.
7. Tighten critic style and truthfulness rules.
8. Integrate context notes into generation.
9. Clarify ATS display behavior.
10. Ensure DOCX templates reflect the new schema.
11. Add networking safety guardrails.

**Claude Code should:**

1. Update `ETPS_PRD.md` with the new sections and notes.
2. Update `IMPLEMENTATION_PLAN.md` Sprints 5–10 with the new tasks and acceptance criteria.
3. Keep Sprints 1–4 and existing completed code intact.
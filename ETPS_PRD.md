# Enterprise-Grade Talent Positioning System (ETPS)
**An AI-Orchestrated Resume, Cover Letter, and Networking Intelligence Platform**  
Author: Benjamin Black  
Version: 1.0 — December 2025

---

## 1. Vision & Target Users

### 1.1 Vision

The Enterprise-Grade Talent Positioning System (ETPS) is a multi-agent, AI-driven system that:

- Tailors resumes and cover letters to specific roles while preserving professional `.docx` formatting.
- Evaluates role fit and **skill gaps** against job descriptions.
- Surfaces company and networking intelligence (likely hiring managers, warm contacts).
- Tracks applications and supports follow-up workflows (future phases).

ETPS is designed to demonstrate enterprise-grade AI systems thinking: multi-agent orchestration, structured data modeling, critic-driven refinement, and real business value.

### 1.2 Target Users

- **Initial user:** Benjamin Black (single-user mode).
- **Future users:** Senior professionals, consulting firms, internal talent/HR teams, and career services organizations.

Architecture must not preclude multi-user support (tenancy) in later phases.

### 1.3 System Behavior

- **Hybrid interaction model:**
  - Primary path: one-shot high-quality output for resume + cover letter.
  - Optional controls for regeneration and refinement (tone, length, style).
  - Minimal friction: paste JD / URL → optional context → generate.

The job intake UI and backend must support an optional free-text "context notes" field. These notes are passed to:

- Summary Rewrite Engine
- Resume bullet selection (for special emphasis or exclusions)
- Cover Letter Generator
- Networking/Outreach Generator (when implemented)

Context notes may include things like:
- "Mention that I spoke with John Smith at the XYZ conference."
- "Do not lean heavily on defense work for this company."

### 1.4 Phase 1 Success Metrics

- Generate polished, ATS-friendly, tailored resumes in < 60 seconds.
- Reduce manual rewriting time by ~90% per application.
- Produce cover letters that are "sendable" with at most minor edits.
- Preserve docx formatting with zero layout breakage.
- Provide **skill-gap analysis** that accurately highlights missing skills and opportunities to reposition, without discouraging applications.

The UI must display ATS-related feedback as:

- A numeric ATS score (0–100).
- A color-coded indicator (e.g., red < 60, yellow 60–75, green > 75).
- A short explanation of which areas are limiting ATS performance (e.g., missing key skills, low keyword overlap in summary).

### 1.5 Long-Term System Feel

- Feels like an internal, enterprise-grade talent tool.
- Good enough polish to show live in interviews and as a consulting asset.
- Demonstrates product thinking, UX design, and AI architecture capabilities.

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
   - Critic enforces truthfulness constraints by validating employer names, job titles, employment dates, and locations against the stored `employment_history` data model.
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

---

## 2. Resume Inputs, Outputs & Data Model

### 2.1 Source of Truth

- **Formatting source of truth:** a master `.docx` resume template.
- **Content source of truth:** a structured JSON/DB model that stores:
  - Roles
  - Bullets
  - Projects
  - Skills
  - Education
  - Metadata (tags, scores, usage, etc.)

Docx controls layout and styling; JSON controls text content and structure.

### 2.2 Template Strategy

- **Phase 1:** one master template (.docx).
- **Phase 2+:** support multiple templates (e.g., AI Governance, Consulting, Product) via a `templates` table and separate docx files.

### 2.3 Hard Formatting Constraints (Non-Negotiable)

The system must preserve the following from the master template:

- Font family and size ranges.
- Page margins and line spacing.
- Bullet style (•, indentation).
- Section order (Summary → Experience → Education → Skills → optional sections) unless overridden by a different template.
- Header layout (name, contact details, links).
- Job title/company/date alignment.
- No auto-resizing, unexpected line breaks, or layout shifts.

### 2.4 Allowed Transformations

The system **may** change per job:

- Summary text and length.
- Bullet selection, rewriting, and ordering inside each role.
- Number of bullets per role.
- Skills section content (which skills to show) and ordering.
- Project and achievement ordering/emphasis.

The system **must never** change:

- Job titles.
- Employer names.
- Dates of employment.
- Locations.
- Degrees and credential facts.

### 2.5 Output Formats

**Phase 1:**

- `.docx` — primary, formatting-preserving resume.
- `text/plain` — ATS/web form friendly version.
- `application/json` — structured representation of selected bullets, skills, and sections.

**Future:**

- PDF (from docx).
- Optional diff views (or rely on Word’s native comparison).

### 2.6 Bullet & Experience Metadata

Each bullet/experience in the JSON/DB model includes:

- **Text:** canonical/original text.
- **Tags:** role type, industry, capability (e.g., `ai_governance`, `financial_services`, `consulting`, `product`, `cloud`).
- **Seniority level:** e.g., `director`, `senior_ic`.
- **Type:** `achievement`, `responsibility`, `metric_impact`.
- **Relevance scores:** to typical role types.
- **STAR notes:** optional longer-form context to support richer rewrites.
- **Usage metadata:**
  - `usage_count`
  - `last_used_at`
  - `retired` (boolean)
- **Version history:** list of improved variants (LLM-generated) with references to the original.

### 2.7 Job & Company Profile Models

**Job profile (`job_profile`) includes:**

- Raw JD text and URL.
- Parsed fields: title, location, seniority, responsibilities, requirements, “nice to haves”.
- Extracted skills and capabilities.
- **Core priorities** (LLM distilled): what this role really cares about.
- **Must-have vs. nice-to-have** capabilities.
- **Skill-gap analysis:** comparison of JD requirements vs. user’s skills/experience, including:
  - Matched skills.
  - Missing or weaker skills.
  - Suggested positioning strategies to address gaps.
- Tone/organizational style inference (conservative, innovative, etc.).
- Links to:
  - `company_id`
  - job-type tags (`ai_governance`, `consulting`, `product`, etc.).

**Company profile (`company_profile`) includes:**

- Name, website, industry, size band, HQ.
- Summary of business lines and markets.
- Known initiatives and transformations (if inferable).
- Culture signals (e.g., formal, mission-driven, experimental).
- Data/AI maturity notes (low, developing, advanced — when inferable).
- Relationship to multiple `job_profile` entries for the same company.

These profiles persist and are reused across applications.

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
   - Less relevant engagements should be omitted from the tailored resume unless user-provided context notes explicitly request their inclusion.

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

---

## 3. Cover Letter Logic

### 3.1 Template Strategy

The system uses a **learning-based template strategy**:

- User-approved cover letters are stored as examples with metadata.
- For a new job, ETPS retrieves the top 1–3 most similar approved letters via embeddings.
- Retrieved examples guide structure and tone (they are not copy-pasted).

The UI exposes style presets:

- **Standard** (~300 words).
- **Executive** (~250 words).
- **Ultra-tight** (~150–200 words).
- **Custom** — uses a free-text instructions field.

### 3.2 Structure & Word Count (Adaptive)

Default: **adaptive**.

- System chooses word range and structure based on:
  - Role seniority.
  - Company culture signals.
  - User’s selected style preset.
- Free-text instructions (e.g., “Mention that I met John Smith at XYZ conference.”) must be incorporated where appropriate.

### 3.3 Required Content Elements

Every cover letter must:

- Explicitly address the top 2–3 JD requirements.
- Connect Benjamin’s experience to the company’s mission/industry.
- When possible, highlight a capability that addresses a plausible team or company challenge (based on job_profile and company_profile).

The system decides which projects/achievements to mention unless overridden by user instructions.

### 3.4 Tone Requirements

Tone must be:

- Executive.
- Direct.
- Concise.
- Outcome-driven (impact and results, not just duties).
- Informed by company culture signals.

### 3.5 Banned Phrases & Stylistic Constraints

The system must never use:

- “I am writing to express my interest…”
- “Passionate”
- “Dynamic professional”
- “I believe I would be a great fit…”
- “Per your job description…”
- Fluffy adjectives like “fast-paced,” “motivated,” “driven.”
- **Em-dashes (—)** — not allowed, under any circumstances.

The critic agent is responsible for enforcing these constraints.

### 3.6 Use of Job & Company Profiles

Cover letters must leverage job_profile and company_profile:

- Job core priorities → which experiences and capabilities to emphasize.
- Company summary & mission → “why this company” logic.
- Culture signals → tone and phrasing.
- Data/AI maturity → which frameworks and achievements to highlight.

### 3.7 Critic & Refinement Loop for Cover Letters

Flow:

1. Generate initial cover letter.
2. Critic evaluates against rubric:
   - Tone.
   - Structure.
   - Required elements.
   - Banned phrases / formatting.
   - Truthfulness.
   - ATS keyword coverage and score.
3. If issues: revise and re-critique (up to 3 passes).
4. Output final docx + text + JSON.

---

## 4. Critic Agent & ATS Rubric

### 4.1 Scope of Critique

The Critic Agent evaluates:

- Resume content and structure.
- Resume docx formatting integrity.
- Cover letter content.
- Cover letter docx formatting integrity.
- Job_profile and company_profile extraction quality.
- Presence of banned phrases or em-dashes.
- Tone adherence.
- Truthfulness (no invented employers, roles, metrics).
- ATS keyword coverage and estimated ATS score vs. JD.

### 4.2 Strictness Level

Mode: **Highly strict.**

- Rejects outputs with banned phrases.
- Rejects mismatch to top JD requirements.
- Rejects hallucinated or exaggerated factual claims.
- Ensures ATS score exceeds a configurable threshold.
- Enforces style and formatting rules strongly.

### 4.3 Rubric Categories

**Resume rubric includes:**

- Alignment to JD requirements.
- Clarity and conciseness of bullets.
- Impact orientation (achievements, metrics).
- Tone (executive, direct, professional).
- Formatting fidelity in docx.
- No hallucinations.
- ATS keyword coverage & score.
- Skills relevance and signal.
- Avoidance of redundant bullets.
- Proper action verbs.
- Clean sentence length and structure.

The Critic must validate the following truthfulness constraints for resumes:

- Employer names and job titles must exactly match stored `employment_history` records.
- Employment dates must exactly match stored date ranges.
- Locations must not be altered.
- No new employers, roles, or degrees may appear that do not exist in the underlying data model.

Any violation is a critical failure and must trigger regeneration or a warning that the request cannot be fulfilled as written.

**Cover letter rubric includes:**

- Tone match (executive, concise, outcome-oriented).
- Structure (intro → value → requirements alignment → close).
- No banned phrases or em-dashes.
- Explicit alignment with 2–3 top JD requirements.
- Integration of job_profile core priorities.
- Integration of company mission/industry themes.
- Incorporation of user instructions.
- Truthfulness and coherence.
- ATS keyword coverage & score.
- Formatting fidelity in docx.

### 4.4 Iteration Policy

- **Adaptive refinement:** generate → critique → revise.
- Stop when:
  - All rubric checks pass.
  - ATS score exceeds threshold.
  - Max iterations (default 3) reached.

### 4.5 Error Handling

- Automatic retry for:
  - Formatting failures.
  - Banned phrases.
  - Em-dash detection.
  - Missing required elements.
  - Low ATS scores.

- Soft fail with explanation when:
  - Formatting cannot be fixed after 3 tries.
  - Repeated hallucinations / extraction failures.
  - JD too ambiguous to parse reliably.

Critic returns a narrative diagnostic for soft failures.

### 4.6 Logging

- Full structured logs of:
  - Critic scores.
  - Reasons for revisions.
  - ATS scores.
  - Failure categories.

Stored in SQLite (and optionally JSON files) for analysis.

### 4.7 Learning from Approved Outputs

- Approved resumes and cover letters are stored with metadata.
- For new requests, similar approved outputs are retrieved via Qdrant.
- Critic compares current output against best historical examples to avoid quality regressions.

### 4.8 Style Enforcement (Critic Requirements)

The critic must enforce strict style compliance for both resumes and cover letters.
Style validation includes both deterministic rules and LLM-based assessments.

**Tone Requirements**
- Executive, direct, concise tone
- Minimal passive voice
- No emotional, fluffy, or filler adjectives
- Professional and outcome-oriented

**Structural Requirements (Cover Letter)**
1. Value-oriented opening
2. Alignment to 2–3 top JD requirements
3. Company, mission, or industry connection
4. Outcome-focused closing
Failure to include any of these sections results in an immediate style failure.

**Lexical Requirements**
- Prefer strong verbs (led, built, drove, implemented)
- Discourage weak verbs (helped, worked on, assisted)
- Detect prohibited clichés and vague language

**Sentence & Paragraph Constraints**
- Target average sentence length: 14–22 words
- Maximum sentence length: 35 words
- Limit excessive comma usage
- Paragraphs must be compact and purpose-driven

**Prohibited Patterns**
- All banned phrases defined in the PRD
- No em-dashes under any circumstances
- No generic filler constructs
- No ungrounded claims or implied exaggeration

**Scoring**
The critic computes:
- tone_score
- structure_score
- lexical_score
- conciseness_score
- overall_style_score

A total score below 85 results in failed critique and regeneration.
Any critical violation (banned phrase, em-dash, structural gap) results in an automatic failure.

The Critic Agent must treat all style constraints in this section as hard requirements:

- Any banned phrase, em-dash, or structural omission (missing alignment section, missing mission/industry tie-in) constitutes a **critical failure**.
- Critical failures require regeneration or repair until resolved or max iterations reached.

---

## 5. Company Intelligence & Networking

### 5.1 Company Data Inputs

**Phase 2 Sources:**

- From JD: company name, team, reporting hints.
- Web search: website, About/Leadership, news.
- Public data sources (where available): size, industry, products.
- User-pasted text: LinkedIn search results, org snapshots, notes.

**Future Source (Phase 3+):**

- Company docs (reports, earnings, case studies).

### 5.2 LinkedIn Data Handling (Compliant)

- User copies and pastes LinkedIn search results or profiles into the system.
- System may instruct an AI-enabled browser tool (e.g., Atlas) *only when the user explicitly runs it* to view their own LinkedIn; ETPS never directly scrapes LinkedIn on its own.
- When no LinkedIn data is provided, ETPS falls back to title/structure heuristics.

### 5.3 Hiring Manager Inference

Uses:

- JD title and seniority.
- Team keywords.
- Company size and norms.
- Pasted employee titles.
- Reporting hints in JD.
- Patterns learned from prior job_profiles.

Outputs a ranked list of potential hiring managers with:

- Scores.
- Confidence levels.
- Justifications.

### 5.4 Warm Contact Identification

Finds contacts based on:

- Shared schools (MIT, Tufts, Sloan).
- Shared employers (e.g., Fidelity, Santander).
- Shared industries (FS, consulting, defense).
- 2nd-degree connections (if provided).
- Alumni links.
- Event/conference notes.
- People in adjacent roles/teams.

Each contact gets:

- Relationship strength score.
- Relevance score.
- Role compatibility score.

### 5.5 Networking Output Formats

The system produces:

- Ranked lists of hiring managers and contacts.
- JSON objects for internal reuse.
- Narrative summaries (“how the org is likely structured and who matters”).
- Docx report: “Networking Plan for <Company>”.
- Action item lists: who to message and when.
- Relationship strength metrics and referral suggestions when scores exceed a threshold.

### 5.6 Outreach Message Generation

Supports:

- Short LinkedIn connection notes.
- Longer InMail-style messages.
- Email variants.
- Tailoring by recipient type:
  - Hiring manager.
  - Recruiter.
  - Peer.
  - Alumni.
  - Former colleague.

Includes a free-text context field (e.g., “Ask about their wife, Samantha”), and messages must incorporate this where appropriate.

### 5.7 Integration With Resume & Cover Letter

Company intelligence influences:

- Which bullets are selected/emphasized.
- How the summary is rewritten.
- Cover letter themes and emphasis.
- Recommendations to seek referrals when relationship scores are high.

### 5.8 Application Tracking (Phase 3)

Tracks:

- Company & job.
- Application status.
- Contacts reached.
- Tasks and reminders.
- Timeline and outcomes.
- Resume/CL versions used.

**Note:** Application tracking, contact history, and reminder workflows are **Phase 3 features**. Phase 1 will only log generation events and critic results; no full tracking UI or workflows are required until Phase 3.

### 5.9 Risk Controls

- Do not over-assert knowledge of company strategy.
- Mark uncertain inferences and include confidence scores.
- Avoid suggesting outreach to CxO-level leaders unless the role/company context clearly justifies it or user insists.

Networking and outreach generation must:

- Avoid recommending outreach to C-level executives unless the role is clearly senior enough and the user explicitly opts in.
- Label any inferred org structure or reporting lines with confidence levels.
- Avoid specific claims about internal strategies, restructurings, or confidential initiatives unless they are directly grounded in user-provided context.

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

---

## 6. Architecture & Implementation

### 6.1 Stack Overview

- **Backend:** Python (FastAPI or similar).
- **Frontend:** Next.js (TypeScript) with Tailwind + shadcn/ui.
- **Vector store:** Qdrant (local instance).
- **Relational store:** SQLite (Phase 1–2).

### 6.2 Storage

SQLite tables for:

- `users` (future multi-user).
- `templates`.
- `bullets` / `experiences`.
- `job_profiles`.
- `company_profiles`.
- `applications`.
- `contacts`.
- `logs`.

Generated `.docx` and JSON files stored on disk or in minimal object storage as needed.

### 6.3 Vector Store

Qdrant local instance for:

- Bullet retrieval.
- Approved letter retrieval.
- Job similarity.
- Company similarity.
- Contact similarity.

### 6.4 Model Configuration

Configurable model selection via `config.yaml`:

- `premium_model` (default: Claude Sonnet/Opus).
- `fallback_model` (e.g., GPT-4o).
- `embedding_model` (e.g., economical embedding provider).
- `scoring_model` for ATS/quick checks.

### 6.5 Runtime & Deployment

- **Development:** local backend + frontend.
- **Deployment:** backend on Railway, frontend on Vercel; Qdrant + SQLite bundled with backend.

### 6.6 UI/UX

**Phase 1 (Portfolio polish):**

- Job intake page (JD URL/text + context notes).
- Buttons to generate resume + cover letter.
- Download buttons for docx, text, JSON.
- Panel to display skill-gap analysis and JD alignment.

**Phase 2:**

- Company & networking view.
- Application history view (read-only initially).

**Optional later (SaaS polish):**

- Micro-interactions, transitions.
- Mobile responsiveness.
- Rich dashboards/visualizations.

### 6.7 Repo Structure

Monorepo:

- `/backend`
- `/frontend`
- `/configs`
- `/docs`
- `/scripts`

### 6.8 Observability

Full structured logging of:

- Critic decisions.
- ATS scores.
- Extracted entities.
- Failure modes.

Stored in SQLite and/or JSON log files.

### 6.9 Configuration Management

- API keys & secrets → environment variables.
- Behavior and thresholds → `config.yaml` / `config.json`.
- Optional user-specific settings → DB if multi-user.

### 6.10 Extensibility

Architecture supports:

- Multi-user tenancy later.
- Additional resume templates.
- Expanded tracking workflows.
- Browser automation (Atlas) modules.
- Company enrichment plugins.
- Notifications (email/calendar).

---

## 7. Future Phases, Positioning & Monetization

### 7.1 Multi-User Support

Planned for future, not enabled by default, but database and auth design should not prevent it.

### 7.2 Roadmap Highlights

- **Phase 1 (Core):**
  - Resume tailoring.
  - Cover letter generation.
  - Critic + ATS scoring.
  - **Skill-gap analysis.**

- **Phase 2:**
  - Company intelligence.
  - Hiring manager inference.
  - Networking suggestions and outreach drafts.

- **Phase 3:**
  - Application tracking and reminders.
  - Calendar/email integration.
  - Interview prep modules.
  - Browser automation.

### 7.3 Monetization Paths

- One-time license for individuals.
- Premium add-ons (networking module, tracking, interview prep).
- B2B/educational licensing (MBA programs, career services).
- Consulting asset (demonstration toolkit).

### 7.4 Positioning & Name

**Name:** Enterprise-Grade Talent Positioning System (ETPS)  
**Tagline:** An AI-Orchestrated Resume, Cover Letter, and Networking Intelligence Platform.

### 7.5 Polish Expectations

Target: **Portfolio polish**, with a clearly defined path to SaaS polish as time allows.

### 7.6 Demo & Portfolio Assets

- Live demo URL (Railway + Vercel).
- Sanitized GitHub repo with this PRD, architecture notes, and code.
- Project page on projects.benjaminblack.consulting.
- Optional demo video and white-paper / case study.

### 7.7 Narrative

ETPS is intended to show that Benjamin can:

> “Design and implement carefully crafted, enterprise-grade AI systems that solve meaningful business problems using cutting-edge AI technologies, data modeling, and multi-agent architectures.”

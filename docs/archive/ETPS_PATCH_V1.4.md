content = """# ETPS_PATCH_v1.4
**Title:** Gap Analysis & Patch Plan – PII Handling for Company Intelligence, Contacts, and Networking  
**Author:** ChatGPT (paired with Benjamin Black)  
**Date:** December 2025  

---

## 1. Scope

This patch focuses on one cross-cutting gap that is **not fully specified** in the current PRD and PLAN:

> How ETPS handles **person-level PII** (names, titles, emails, LinkedIn URLs, notes) used for company intelligence, contacts, and networking – especially in **logs, vector stores, and model prompts**.

The goal is to preserve the high-value behavior in PRD Sections **5.1–5.8** (company intelligence, warm contact identification, networking outputs, outreach) while tightening privacy, compliance, and future multi-user readiness.

The patch **does not** change the UX expectations in the PRD. It changes **where and how PII is stored and referenced**.

---

## 2. Gap Analysis vs PRD & PLAN

### 2.1 Where PII Shows Up in the PRD

PII appears or is implied in the following PRD sections:

- **5.2 LinkedIn Data Handling (Compliant)**  
  > “User copies and pastes LinkedIn search results or profiles into the system.”  
  This includes names, titles, companies, profile URLs, and potentially locations and contact info.

- **5.3 Hiring Manager Inference**  
  > “Outputs a ranked list of potential hiring managers with scores, confidence levels, and justifications.”  
  These outputs inherently contain person names, titles, and companies.

- **5.4 Warm Contact Identification**  
  > “Finds contacts based on shared schools, shared employers, industries, 2nd-degree connections, alumni, etc.”  
  Again, this depends on person-level PII and relationship notes.

- **5.5 Networking Output Formats / 5.6 Outreach Message Generation / 5.7 Integration With Resume & Cover Letter**  
  These sections assume ETPS can generate **named outreach messages** and **networking plans** that contain PII.

- **5.8 Application Tracking (Phase 3)**  
  Tracks contacts, outreach, and status over time – which implies **persistent storage** of person-level PII.

Nowhere in these sections is there a **clear data-classification or storage boundary** that distinguishes:

1. **Authoritative PII repositories** (where real names live), vs  
2. **Derived artifacts** (logs, vector store entries, training examples) where PII should be minimized or replaced.

### 2.2 Where PII Shows Up in the PLAN

The PLAN references:

- `contacts` tables and networking services.
- Vector store usage for **approved outputs** and **similarity retrieval**.
- Extensive logging (critic logs, output logs, application logs).

But it does **not** explicitly state:

- Whether **full names** and contact PII are allowed in **Qdrant**.
- Whether logs can store PII verbatim.
- How to handle **multi-user** scenarios, where contact PII for one user must not be leaked to another.

### 2.3 Risk if Unpatched

If left as-is, a straightforward implementation would likely:

- Store **full names and contact info** in:
  - SQLite (`contacts`, `applications`, `networking` tables),
  - **Vector store** documents (approved outputs, networking examples),
  - **Logs** (critic logs, debugging traces).
- Include **raw LinkedIn snippets** as text in vector embeddings and logs.

This creates several problems:

1. **Over-exposed PII**  
   Names, titles, and notes end up in multiple storage systems that are harder to rotate or delete.

2. **Harder data-subject deletion**  
   If a user wants a contact removed, it’s much harder to clear them from embeddings/logs than from a single authoritative DB table.

3. **Multi-tenant risk (future)**  
   Without clear boundaries, PII from User A could influence retrieval for User B if the system is ever extended to multi-user mode.

4. **Auditability & compliance**  
   No explicit place to implement retention policies or “right to be forgotten” logic for contacts.

---

## 3. Design Principle for PII in ETPS

**Principle:**  
> Keep **real person identities** (names, titles, contact info) in a **single authoritative store** (relational DB).  
> Everywhere else (vector store, logs, analytics) use **stable pseudonymous identifiers + minimal context**, and only re-join to PII at the very edge where user-visible outputs are generated.

Concretely:

- **DB = Source of truth for PII.**  
  Names, titles, relationships, private notes live here.

- **Vector store & logs = pseudonymized.**  
  They only see:
  - Stable **contact_id** (e.g., UUID),
  - Sanitized snippets with PII replaced by tags (e.g., `{{CONTACT_NAME}}`),
  - Non-identifying features (industry, seniority, role archetype, relationship strength buckets).

- **Re-attach real names** only when rendering final networking plans and outreach messages for the **current user**, in memory.

---

## 4. Patch Requirements (Spec-Level)

This section defines **concrete changes** to the PRD/PLAN behavior without breaking the intended features.

### 4.1 New Data-Classification Rules

Add the following as a **global data-handling rule** (PRD Section 5 or new Section 8):

1. **Authoritative PII Store (Relational DB)**
   - `contacts` table holds:
     - `id` (UUID),
     - `user_id` (owner),
     - `full_name`,
     - `current_title`,
     - `company_name`,
     - `email` (optional),
     - `linkedin_url` (optional),
     - `notes` (user-provided),
     - `relationship_strength` (0–100),
     - `created_at`, `updated_at`, `deleted_at` (soft delete).
   - PII **must not** be stored in vector store payloads or logs as raw text.

2. **Pseudonymous Identifiers in Derived Artifacts**
   - All vector store documents referencing a person must use:
     - `contact_id` (UUID),
     - Non-PII attributes: e.g., `role_archetype` (“Head of Data”, “Director, AI”), `company_industry`, `seniority_band`, `relationship_bucket` (“warm”, “cold”).
   - Any phrase that contained a real name in an example or approved output must be **normalized** to a token:
     - `"Hi Sarah,"` → `"Hi {{CONTACT_NAME}},"`
     - `"Sarah Johnson"` → `"{{CONTACT_NAME}}"`.

3. **Logs & Diagnostics**
   - Critic logs, error logs, and analytics logs should **never** include raw names or emails.
   - Where necessary, they store:
     - `contact_id`,
     - `application_id`,
     - anonymized excerpts with `{{CONTACT_NAME}}`.

4. **Model Prompts**
   - LLM prompts may contain:
     - **Company names** and public roles,
     - Pseudonymous tags for contacts (e.g., `{{CONTACT_NAME}}`, `{{HIRING_MANAGER}}`),
   - Real names may be injected **only at final rendering**, not inside logs or vector documents.

### 4.2 Changes to PRD Section 5 (Company Intelligence & Networking)

Add a subsection:

> **5.11 PII Handling for Contacts & Networking**  
> - Person-level PII (names, emails, LinkedIn URLs, free-text notes) is stored only in the relational database as the **authoritative source of truth**.  
> - All secondary stores (vector embeddings, logs, analytics) must use pseudonymous `contact_id` references and normalize names to placeholders (e.g., `{{CONTACT_NAME}}`).  
> - Networking and outreach generators receive `contact_id` + structural context; they re-attach real names and emails only at the final text rendering step.  
> - All networking features must be scoped to a specific `user_id` so that contact PII from one user cannot be returned in another user’s results, even if the system later supports multi-tenant use.

### 4.3 Changes to PLAN (Implementation Plan)

Amend the PLAN with the following **additional tasks**.

#### 4.3.1 DB & Schema (Phase 2 / Sprint 13+)

- Add `contacts` schema details:
  - Ensure `full_name`, `email`, `linkedin_url`, and notes are in **SQLite only**.
  - Add `deleted_at` for soft deletion and future “right to be forgotten.”

- Update `ApprovedOutput` and any networking-related models:
  - Store `contact_id` and placeholder-normalized text instead of raw names.

#### 4.3.2 Vector Store (Phase 2 – Networking)

- When indexing **approved networking outputs** or **company intelligence examples**:
  - Replace all detected names with tokens:
    - Use a simple deterministic sanitizer to swap `"Jane Doe"` → `"{{CONTACT_NAME}}"`.
  - Store only:
    - `contact_id` (for the owning user),
    - non-PII features (industry, role archetype, seniority band),
    - normalized text for retrieval.

- Retrieval returns:
  - Example snippets with placeholders,
  - Metadata including `contact_id` for the **current user only** (no cross-user leakage).

#### 4.3.3 Logging & Observability

- Update critic and networking logs:
  - Replace names with `{{CONTACT_NAME}}` before logging.
  - Only log `contact_id`, `application_id`, scores, and anonymized text.

- Add tests to ensure:
  - No log line in `tests` can contain a literal example contact name.
  - A helper function `sanitize_personal_identifiers(text: str) -> str` is applied at log boundaries.

#### 4.3.4 Networking & Outreach Generators

- **Input:**  
  - job + company context,  
  - contact structural metadata (seniority, relationship_strength, in/out of company),  
  - `contact_id` (no real name in prompt).

- **Generation flow:**
  1. LLM generates outreach using placeholders like `{{CONTACT_NAME}}` and `{{CONTACT_COMPANY}}`.
  2. A final **rendering step** replaces placeholders with actual values from the DB **only for the current user session**.
  3. Rendered text is returned to the client; placeholder versions may optionally be indexed for future semantic retrieval.

- **Approved Outputs:**
  - When a user approves an outreach message for reuse:
    - The system stores a **sanitized version** (with placeholders) as the example body.
    - The original, fully named text is kept only in the `applications` / `contacts` tables if needed, not in the vector store.

---

## 5. Security & Compliance Implications

### 5.1 Benefits

- **Narrow PII blast radius:**  
  Most person data lives in one place (SQLite) with clear backup and deletion semantics.

- **Easier multi-tenant future:**  
  All networking functionality is scoped by `user_id` and `contact_id`, naturally limiting cross-user leakage.

- **Safer vector store usage:**  
  Qdrant holds only abstracted contact semantics and placeholders, not raw PII.

- **Cleaner audit story:**  
  “PII is stored only in `contacts` (and closely related tables); all other stores are pseudonymous.”

### 5.2 Remaining Risks (Explicit)

- **Device & client copies:**  
  Once outreach text is generated with real names and downloaded, ETPS cannot control local copies.

- **User-pasted content:**  
  If the user pastes raw LinkedIn html/snippets into free-text notes, the sanitizer must run before indexing/logging.

---

## 6. Implementation Checklist

This checklist summarizes the **minimum set of changes** needed to implement this patch:

1. **Schema**
   - [ ] Ensure `contacts` table is the only place that stores full names, emails, and LinkedIn URLs.
   - [ ] Add `deleted_at` and `user_id` to `contacts` if not already present.

2. **Vector Store**
   - [ ] Implement `sanitize_personal_identifiers()` helper.
   - [ ] Apply sanitization before indexing any text that may contain names.
   - [ ] Ensure vectors store `contact_id` + non-PII features only.

3. **Logs**
   - [ ] Wrap all critic/networking logging calls with sanitization.
   - [ ] Confirm no PII appears in structured logs by test.

4. **LLM Prompts**
   - [ ] Introduce placeholders (`{{CONTACT_NAME}}`, `{{CONTACT_COMPANY}}`) in networking prompts.
   - [ ] Add a final rendering layer that re-injects names using DB lookups.

5. **Tests**
   - [ ] Add tests for:
     - Sanitization of example text,
     - No raw names in vector payloads,
     - No raw names in critic/networking logs,
     - Correct placeholder substitution at render time.

---

## 7. Summary

This patch **does not remove** any functionality described in PRD Sections 5.1–5.8. ETPS still:

- Infers hiring managers,
- Identifies warm contacts,
- Generates tailored outreach,
- Integrates networking insights into resumes and cover letters.

What changes is **how identities are handled internally**:

- Real names are stored and managed in **one authoritative place** (the relational DB),
- All derived artifacts (vectors, logs, approved examples) operate on **pseudonymous IDs and placeholders**,
- Names are only re-attached **on the edge**, when generating final user-visible networking outputs.

This keeps ETPS simple enough to build and reason about now, while aligning with enterprise-grade expectations for **privacy, data minimization, and future multi-tenant safety**.
"""

with open("ETPS_PATCH_v1.4.md", "w") as f:
    f.write(content)

"ETPS_PATCH_v1.4.md written"

# ETPS Data Model Reference

**Version:** 1.4.3
**Last Updated:** December 2025
**Source:** `backend/db/models.py`
**Phase Status:** Phase 1A-1C Complete (Deployed to Railway + Vercel)

---

## Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER                                            │
│  id, username, email, full_name, phone, location                            │
│  candidate_profile (JSON)                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
       │              │              │              │              │
       │1:N           │1:N           │1:N           │1:N           │1:N
       ▼              ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Template │   │Experience│   │  Bullet  │   │JobProfile│   │  Contact │
└──────────┘   └────┬─────┘   └──────────┘   └────┬─────┘   └──────────┘
                    │                              │
                    │1:N                           │1:N
                    ▼                              ▼
              ┌──────────┐                   ┌──────────┐
              │Engagement│                   │Application│
              └────┬─────┘                   └──────────┘
                   │
                   │1:N
                   ▼
              ┌──────────┐
              │  Bullet  │ (engagement-level)
              └──────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPANY PROFILE                                      │
│  (Optional - links to JobProfile, Application, Contact)                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUDIT / LEARNING                                     │
│  LogEntry, CriticLog, ApprovedOutput                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Entities

### User
The central entity - each user has their own resume content and applications.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Unique identifier |
| username | String(100) | Unique, Not Null | Login username |
| email | String(255) | Unique, Not Null | Email address |
| full_name | String(255) | Not Null | Display name |
| phone | String(50) | Nullable | Contact phone |
| portfolio_url | String(500) | Nullable | Portfolio website |
| linkedin_url | String(500) | Nullable | LinkedIn profile |
| location | String(255) | Nullable | Geographic location |
| candidate_profile | JSON | Nullable | See schema below |
| is_active | Boolean | Default: True | Account status |
| created_at | DateTime | Auto | Creation timestamp |
| updated_at | DateTime | Auto on update | Last modification |

**candidate_profile JSON Schema:**
```json
{
  "primary_identity": "AI Strategy Leader",
  "specializations": ["AI Governance", "Data Strategy"],
  "target_roles": ["Director", "VP"],
  "linkedin_meta": {
    "headline": "...",
    "about": "...",
    "top_skills": ["..."],
    "open_to_work_titles": ["..."]
  },
  "ai_portfolio": [
    {
      "name": "Project Name",
      "description": "...",
      "tech_stack": ["Python", "LangChain"],
      "impact": "40% improvement",
      "fs_relevance": 0.8
    }
  ],
  "ai_systems_builder": true
}
```

---

### Experience
Work experience entry (job role) on a resume.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Unique identifier |
| user_id | Integer | FK(users.id), Not Null | Owner reference |
| job_title | String(255) | Not Null, **Immutable** | Job title |
| employer_name | String(255) | Not Null, **Immutable** | Company name |
| location | String(255) | Nullable, **Immutable** | Work location |
| start_date | Date | Not Null | Role start date |
| end_date | Date | Nullable | Role end (null = current) |
| description | Text | Nullable | Role description |
| order | Integer | Default: 0 | Display order (lower = higher) |
| employer_type | String(50) | Nullable | `independent_consulting`, `full_time`, `contract` |
| role_summary | Text | Nullable | Brief role summary |
| ai_systems_built | JSON | Nullable | List of AI systems created |
| governance_frameworks_created | JSON | Nullable | Governance frameworks |
| fs_domain_relevance | Float | Nullable | Financial services relevance (0.0-1.0) |
| tools_and_technologies | JSON | Nullable | Tech stack used |

**Relationships:**
- `user` → User (many-to-one)
- `engagements` → Engagement[] (one-to-many, cascade delete)
- `bullets` → Bullet[] (one-to-many, cascade delete)

**Business Rules:**
- `job_title`, `employer_name`, `location` are **immutable** (truthfulness constraint)
- Consulting roles (`employer_type = 'independent_consulting'`) use Engagements
- Non-consulting roles have Bullets directly attached

---

### Engagement
Client engagement within a consulting role.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Unique identifier |
| experience_id | Integer | FK(experiences.id), Not Null | Parent experience |
| client | String(255) | Nullable | Client name (null for internal) |
| project_name | String(500) | Nullable | Project title |
| project_type | String(100) | Nullable | `advisory`, `product_build`, `implementation` |
| date_range_label | String(100) | Nullable | Display date (e.g., "2023", "Q1 2024") |
| domain_tags | JSON | Nullable | Domain categories |
| tech_tags | JSON | Nullable | Technologies used |
| order | Integer | Default: 0 | Display order within experience |

**Relationships:**
- `experience` → Experience (many-to-one)
- `bullets` → Bullet[] (one-to-many, cascade delete)

---

### Bullet
Individual bullet point describing an achievement or responsibility.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Unique identifier |
| user_id | Integer | FK(users.id), Not Null | Owner reference |
| experience_id | Integer | FK(experiences.id), Not Null | Parent experience |
| engagement_id | Integer | FK(engagements.id), Nullable | Parent engagement (consulting only) |
| text | Text | Not Null | Bullet content |
| tags | JSON | Nullable | Skill/topic tags |
| seniority_level | String(50) | Nullable | `director`, `senior_ic`, etc. |
| bullet_type | String(50) | Nullable | `achievement`, `responsibility`, `metric_impact` |
| relevance_scores | JSON | Nullable | Tag → score mapping |
| star_notes | Text | Nullable | STAR method notes |
| usage_count | Integer | Default: 0 | Times used in applications |
| last_used_at | DateTime | Nullable | Last usage timestamp |
| retired | Boolean | Default: False | Soft delete flag |
| version_history | JSON | Nullable | List of previous versions |
| embedding | JSON | Nullable | 384-dim vector |
| importance | String(20) | Nullable | `high`, `medium`, `low` |
| ai_first_choice | Boolean | Default: False | Prioritize for AI roles |
| order | Integer | Default: 0 | Display order |

**relevance_scores JSON Schema:**
```json
{
  "ai_governance": 0.85,
  "consulting": 0.70,
  "python": 0.60
}
```

**version_history JSON Schema:**
```json
[
  {
    "text": "Previous version text",
    "created_at": "2025-01-15T10:30:00",
    "strategy": "keywords",
    "job_profile_id": 123
  }
]
```

**Indexes:**
- `ix_bullets_retired` on retired
- `ix_bullets_engagement` on engagement_id
- Note: `ix_bullets_tags` removed for PostgreSQL compatibility (B-tree cannot index JSON)

---

### JobProfile
Parsed and analyzed job description.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Unique identifier |
| user_id | Integer | FK(users.id), Not Null | Owner reference |
| company_id | Integer | FK(company_profiles.id), Nullable | Company link |
| raw_jd_text | Text | Not Null | Original JD text |
| jd_url | String(1000) | Nullable | Source URL |
| job_title | String(255) | Not Null | Position title |
| location | String(255) | Nullable | Job location |
| seniority | String(100) | Nullable | Level (e.g., "director", "senior") |
| responsibilities | Text | Nullable | Extracted responsibilities |
| requirements | Text | Nullable | Extracted requirements |
| nice_to_haves | Text | Nullable | Optional qualifications |
| extracted_skills | JSON | Nullable | List of required skills |
| core_priorities | JSON | Nullable | LLM-distilled priorities |
| must_have_capabilities | JSON | Nullable | Required capabilities |
| nice_to_have_capabilities | JSON | Nullable | Preferred capabilities |
| skill_gap_analysis | JSON | Nullable | Gap analysis result |
| tone_style | String(50) | Nullable | Expected tone |
| job_type_tags | JSON | Nullable | Job categories |
| embedding | JSON | Nullable | 384-dim vector |
| selected_skills | JSON | Nullable | User-ordered skills: [{skill, match_pct, included, order}] (Sprint 10E) |
| key_skills | JSON | Nullable | 3-4 skills for cover letter emphasis (Sprint 10E) |
| capability_clusters | JSON | Nullable | LLM-extracted capability clusters with component skills and evidence (Sprint 11) |
| capability_cluster_cache_key | String(64) | Nullable, Indexed | SHA256 hash of JD text for cluster cache lookup (Sprint 11) |
| capability_analysis_timestamp | DateTime | Nullable | When capability analysis was last performed (Sprint 11) |

**skill_gap_analysis JSON Schema:**
```json
{
  "matched_skills": [
    {"skill": "Python", "match_strength": 0.95}
  ],
  "skill_gaps": [
    {"skill": "Kubernetes", "importance": "nice_to_have"}
  ],
  "positioning_strategies": ["Emphasize cloud migration experience"]
}
```

---

### Application
Job application with generated materials and status tracking.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Unique identifier |
| user_id | Integer | FK(users.id), Not Null | Applicant |
| job_profile_id | Integer | FK(job_profiles.id), Not Null | Target job |
| company_id | Integer | FK(company_profiles.id), Nullable | Company |
| template_id | Integer | FK(templates.id), Nullable | Resume template |
| status | String(50) | Default: 'draft', Not Null | Application status |
| applied_at | DateTime | Nullable | Submission timestamp |
| resume_path | String(500) | Nullable | Generated resume file |
| cover_letter_path | String(500) | Nullable | Generated cover letter file |
| resume_json | JSON | Nullable | TailoredResume structure |
| cover_letter_json | JSON | Nullable | CoverLetter structure |
| ats_score | Float | Nullable | ATS compatibility score |
| critic_scores | JSON | Nullable | Detailed quality scores |
| notes | Text | Nullable | User notes |

**Status Values:**
- `draft` - Initial state
- `applied` - Submitted
- `screening` - Under review
- `interviewing` - In interview process
- `offer` - Received offer
- `rejected` - Not selected
- `withdrawn` - User withdrew

**critic_scores JSON Schema:**
```json
{
  "resume": {
    "passed": true,
    "quality_score": 85.5,
    "alignment_score": 90.0,
    "clarity_score": 82.0,
    "impact_score": 78.0,
    "tone_score": 88.0,
    "ats_overall": 85.0
  },
  "cover_letter": {
    "passed": true,
    "quality_score": 82.0
  }
}
```

---

### CompanyProfile
Company information for application context.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Unique identifier |
| name | String(255) | Unique, Not Null | Company name |
| website | String(500) | Nullable | Company website |
| industry | String(100) | Nullable | Industry sector |
| size_band | String(50) | Nullable | Employee count range |
| headquarters | String(255) | Nullable | HQ location |
| business_lines | Text | Nullable | Business description |
| known_initiatives | Text | Nullable | Strategic initiatives |
| culture_signals | JSON | Nullable | Culture keywords |
| data_ai_maturity | String(50) | Nullable | `low`, `developing`, `advanced` |
| embedding | JSON | Nullable | 384-dim vector |

---

### ApprovedOutput
User-approved generations for learning.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Unique identifier |
| user_id | Integer | FK(users.id), Not Null | Owner |
| application_id | Integer | FK(applications.id), Nullable | Source application |
| job_profile_id | Integer | FK(job_profiles.id), Nullable | Context job |
| output_type | String(50) | Not Null | Output category |
| original_text | Text | Not Null | Approved content |
| context_metadata | JSON | Nullable | Generation context |
| quality_score | Float | Nullable | Quality rating (0.0-1.0) |
| embedding | JSON | Nullable | 384-dim vector |

**output_type Values:**
- `resume_bullet`
- `cover_letter_paragraph`
- `professional_summary`
- `full_resume`
- `full_cover_letter`

---

### Supporting Entities

#### Template
Resume template (DOCX) for generation.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | PK |
| user_id | Integer | FK(users.id) |
| name | String(255) | Template name |
| docx_path | String(500) | File path |
| description | Text | Template description |
| is_default | Boolean | Default template flag |

#### Contact
Professional network contact. **Authoritative PII Store** - all person-level PII (names, emails, LinkedIn URLs) is stored ONLY in this table.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | PK |
| user_id | Integer | FK(users.id) |
| company_id | Integer | FK(company_profiles.id), Nullable |
| full_name | String(255) | Contact name (**PII**) |
| title | String(255) | Job title |
| email | String(255) | Email address (**PII**) |
| linkedin_url | String(500) | LinkedIn profile URL (**PII**) |
| notes | Text | User notes (**may contain PII**) |
| relationship_type | String(50) | Connection type |
| relationship_strength | Float | Connection strength (0.0-1.0) |
| is_hiring_manager_candidate | Boolean | Potential hiring manager |
| deleted_at | DateTime | Soft deletion timestamp (GDPR compliance) |

**PII Handling Notes:**
- Contact is the **single authoritative store** for person-level PII
- Vector stores and logs use pseudonymous identifiers (`contact_id`) only
- Use `utils.pii_sanitizer` to replace names with placeholders before logging/indexing
- Use `services.placeholder_renderer` to restore real names at output time

#### LogEntry
System audit log.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | PK |
| user_id | Integer | FK(users.id), Nullable |
| application_id | Integer | FK(applications.id), Nullable |
| log_type | String(50) | Log category |
| level | String(20) | `debug`, `info`, `warning`, `error` |
| message | Text | Log message |
| log_metadata | JSON | Additional context |

#### CriticLog
Critic evaluation history.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | PK |
| session_id | String(36) | UUID grouping iterations |
| iteration | Integer | Iteration number |
| quality_score | Float | Evaluation score |
| passed | Boolean | Pass/fail status |
| issues | JSON | List of issues found |

---

## Vector Embeddings

The following entities have 384-dimensional embeddings for semantic search:

| Entity | Field | Used For |
|--------|-------|----------|
| Bullet | embedding | Skill matching, similar bullet retrieval |
| JobProfile | embedding | Job similarity search |
| CompanyProfile | embedding | Company matching |
| ApprovedOutput | embedding | Similar approved output retrieval |

**Embedding Model:** `text-embedding-3-small` (OpenAI)
**Dimensions:** 384
**Storage:** Qdrant vector database (collections: `etps_bullets`, `etps_jobs`, `etps_approved_outputs`)

---

## Indexes

| Table | Index Name | Columns | Purpose |
|-------|------------|---------|---------|
| bullets | ix_bullets_retired | retired | Active bullet queries |
| bullets | ix_bullets_engagement | engagement_id | Engagement lookup |
| ~~bullets~~ | ~~ix_bullets_tags~~ | ~~tags~~ | ~~Removed - PostgreSQL B-tree can't index JSON~~ |
| contacts | ix_contacts_company_hiring | company_id, is_hiring_manager_candidate | Hiring manager search |
| log_entries | ix_log_entries_type_level | log_type, level | Log filtering |
| critic_logs | ix_critic_logs_session | session_id, iteration | Session queries |
| critic_logs | ix_critic_logs_quality | quality_score | Score-based queries |
| approved_outputs | ix_approved_outputs_user_type | user_id, output_type | User output lookup |
| approved_outputs | ix_approved_outputs_quality | quality_score | Quality filtering |
| job_profiles | ix_job_profiles_cluster_key | capability_cluster_cache_key | Cluster cache lookup (Sprint 11) |

---

## Migration History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Nov 2025 | Initial schema |
| 1.1.0 | Nov 2025 | Added JobProfile, Application |
| 1.2.0 | Dec 2025 | Added CriticLog, embedding fields |
| 1.3.0 | Dec 2025 | Added Engagement, candidate_profile, ai_first_choice |
| 1.4.0 | Dec 2025 | Added PII handling: Contact.deleted_at, sanitization utilities |
| 1.4.1 | Dec 2025 | Added selected_skills, key_skills to JobProfile (Sprint 10E) |
| 1.4.2 | Dec 2025 | Added capability_clusters, capability_cluster_cache_key, capability_analysis_timestamp to JobProfile (Sprint 11) |
| 1.4.3 | Dec 2025 | PostgreSQL compatibility: removed ix_bullets_tags index (B-tree can't index JSON); added psycopg2-binary driver (Sprint 14) |

---

## PII Handling Architecture

### Design Principle
> Keep **real person identities** (names, titles, emails, LinkedIn URLs) in a **single authoritative store** (Contact table). Everywhere else (vector store, logs, analytics) use **stable pseudonymous identifiers** (`contact_id`) and **placeholders** (`{{CONTACT_NAME}}`), and only re-join to PII at the very edge where user-visible outputs are generated.

### Data Classification

| Location | PII Handling |
|----------|--------------|
| `contacts` table | **Authoritative store** - all PII lives here |
| `approved_outputs` table | Original text in DB; sanitized text in vector store |
| Vector store (Qdrant) | Sanitized text only - names replaced with `{{CONTACT_NAME}}` |
| Log files | Use `utils.logging_helpers.safe_log_*()` to sanitize |
| LLM prompts | Use placeholders; real names injected at render time |

### Sanitization Flow
```
User Input → sanitize_personal_identifiers() → Store in vector/logs
                                                      ↓
Database Query ← placeholder_renderer.render_*() ← Final Output
```

### Key Utilities
| Module | Function | Purpose |
|--------|----------|---------|
| `utils.pii_sanitizer` | `sanitize_personal_identifiers()` | Replace PII with placeholders |
| `utils.pii_sanitizer` | `restore_personal_identifiers()` | Restore from contact map |
| `utils.logging_helpers` | `safe_log_info/debug/warning/error()` | Sanitized logging |
| `services.placeholder_renderer` | `render_networking_output()` | Restore PII at output time |
| `services.placeholder_renderer` | `build_contact_context()` | Non-PII context for prompts |

### Soft Deletion (GDPR)
- `Contact.deleted_at` enables "right to be forgotten"
- Soft-deleted contacts excluded from rendering operations
- Query pattern: `.filter(Contact.deleted_at.is_(None))`

---

## Maintenance Notes

### Adding New Fields
1. Add field to model class in `backend/db/models.py`
2. Update this document with field details
3. Create migration if needed
4. Update affected services
5. Add tests for new field

### Adding New Entities
1. Create model class in `backend/db/models.py`
2. Add to this document (ERD + field table)
3. Create relationships to existing entities
4. Add indexes as needed
5. Update `ARCHITECTURE.md` if significant

### JSON Field Changes
1. Update JSON schema in this document
2. Update Pydantic schemas in `backend/schemas/`
3. Update affected services
4. Add migration for existing data if needed

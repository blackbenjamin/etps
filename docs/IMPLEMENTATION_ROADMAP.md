# ETPS Implementation Roadmap
**Version 1.3.0 Schema Migration + Feature Enhancements**
**Created: December 2025**

---

## Overview

This roadmap covers:
1. Schema v1.3.0 migration (engagement hierarchy, new fields)
2. Resume data update (December 2025 resume)
3. PRD features not yet implemented
4. Improvements from prompt methodology analysis

---

## Phase 1: Schema Migration (Priority: Critical)

### 1.1 Database Schema Updates

| Change | Description | Effort |
|--------|-------------|--------|
| Add `engagements` table | New table: `id`, `experience_id`, `client`, `project_name`, `project_type`, `date_range_label`, `domain_tags`, `tech_tags`, `order` | 2 hours |
| Update `bullets` table | Add `engagement_id` FK (nullable for non-consulting roles) | 1 hour |
| Update `experiences` table | Add `employer_type`, `role_summary`, `ai_systems_built`, `governance_frameworks_created`, `fs_domain_relevance`, `tools_and_technologies` | 1 hour |
| Update `users` table | Add `primary_identity`, `specializations`, `target_roles`, `ai_systems_builder`, `portfolio_url`, `linkedin_meta` (JSON) | 1 hour |
| Update `skills` table structure | Add `category`, `level`, `core` fields | 1 hour |
| Add `education` fields | Add `prestige_weight`, `executive_credibility_score`, `language_fluency` | 30 min |

### 1.2 Pydantic Schema Updates

| File | Changes |
|------|---------|
| `schemas/resume_tailor.py` | Add `Engagement`, update `SelectedRole` to include engagements |
| `schemas/user.py` | Add candidate profile fields |
| `schemas/skill.py` | Add category, level, core |
| `schemas/education.py` | Add prestige/credibility fields |

### 1.3 Migration Script

Create `migrations/v1_3_0_schema_migration.py`:
- Backup existing data
- Create new tables
- Migrate BBC bullets to engagements structure
- Update foreign keys

---

## Phase 2: Resume Data Update (Priority: Critical)

### 2.1 Update User Profile

```python
user.email = "ben@benjaminblack.consulting"
user.phone = "617-504-5529"
user.portfolio_url = "projects.benjaminblack.consulting"
user.primary_identity = "AI & Data Leader"
user.specializations = ["AI Strategy", "AI Enablement", "Enterprise AI Systems Development", ...]
```

### 2.2 Update/Add Experiences

| Experience | Action | Notes |
|------------|--------|-------|
| BBC (10/2025 – Present) | ADD NEW | Independent AI Strategist & Builder |
| KeyLogic (9/2024 – 10/2025) | UPDATE | Dates changed, bullets updated |
| BBC (8/2022 – 9/2024) | ADD NEW | Principal Consultant (Edward Jones, Darling) |
| MANTL (2/2021 – 6/2022) | UPDATE | Minor updates |
| BBC (7/2016 – 1/2021) | UPDATE | Convert existing to engagement structure |
| Knowledgent | UPDATE | Add John Hancock as engagement |
| Santander | UPDATE | No engagements (direct role) |
| Fidelity | KEEP | No changes |

### 2.3 Create Engagements

| Experience | Engagements |
|------------|-------------|
| BBC (2025) | ETPS (internal), Client work (if any) |
| BBC (2022-2024) | Edward Jones, Darling Consulting Group |
| BBC (2016-2021) | Squark, Vestmark, John Hancock, Olmstead, Fidelity |
| Knowledgent | John Hancock Financial Services |

### 2.4 Update Skills

Add new skills with proper categorization:
- AI/ML: RAG, LLM Evaluation, Embeddings, Prompt Engineering
- Governance: AI Governance, Data Governance
- Cloud: AWS (advanced), Azure (advanced), GCP (intermediate)
- Tech: Python, SQL, Spark, MLOps

---

## Phase 3: DOCX Generator Updates (Priority: High)

### 3.1 Section Order Change
- Current: Summary → Experience → Education → Skills
- New: Summary → Experience → Skills → Education

### 3.2 Engagement Formatting in DOCX
For consulting roles, render as:
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

### 3.3 Skills Section Update
New format from resume:
```
AI/ML/Data Science: RAG, LLM Evaluation, Embeddings, Python, R, Spark, MLOps
Cloud/Data Platforms: AWS, Azure, GCP, Snowflake, SQL, Data Governance
BI/Tooling: Power BI, Tableau, Jira
```

---

## Phase 4: Resume Tailor Service Updates (Priority: High)

### 4.1 Engagement-Aware Selection
- Select engagements based on JD relevance
- Select bullets within relevant engagements
- Maintain engagement grouping in output

### 4.2 Bullet Ordering
- Order bullets by relevance score within each engagement
- Most relevant bullets first (per prompt methodology)

### 4.3 ATS Score Implementation
- Implement `ats_score_estimate` field
- Calculate keyword density
- Track missing critical keywords

---

## Phase 5: PRD Features Not Yet Built (Priority: Medium)

### 5.1 Bullet Rewriting (PRD 2.4, 2.6)
| Feature | Description | Effort |
|---------|-------------|--------|
| LLM bullet rewriting | Rewrite bullets to emphasize JD keywords | 1 week |
| Version history | Store bullet variants with original reference | 2 days |
| STAR notes integration | Use STAR context for richer rewrites | 2 days |

### 5.2 Resume Critic (PRD 4.2-4.3)
| Feature | Description | Effort |
|---------|-------------|--------|
| Resume rubric evaluation | Match cover letter critic approach | 1 week |
| Formatting validation | Check DOCX formatting integrity | 2 days |
| Truthfulness checks | No hallucinated content | 1 day |

### 5.3 Learning from Approved Outputs (PRD 4.7)
| Feature | Description | Effort |
|---------|-------------|--------|
| Qdrant integration | Vector store for approved outputs | 3 days |
| Similar output retrieval | Find best historical examples | 2 days |

---

## Phase 6: Enhancement Features (Priority: Lower)

### 6.1 Bullet Analysis Service
- Flag bullets missing metrics
- Identify weak verbs
- Detect generic language

### 6.2 Interactive Enhancement Agent
- Dialogue for STAR notes collection
- Guided metric addition
- Skill gap filling conversations

### 6.3 Phrase Matching to JD
- Extract key phrases from JD responsibilities
- Map to synonym vocabulary
- Suggest rephrasing

---

## Implementation Order

```
Week 1-2: Phase 1 (Schema) + Phase 2 (Data)
  └── Schema migration
  └── Resume data population
  └── Engagement structure

Week 2-3: Phase 3 (DOCX) + Phase 4 (Tailor)
  └── DOCX generator updates
  └── Engagement-aware selection
  └── Section order change

Week 3-4: Phase 5.2 (Resume Critic)
  └── Rubric evaluation
  └── ATS scoring

Week 4-5: Phase 5.1 (Bullet Rewriting)
  └── LLM integration
  └── Version history

Future: Phase 5.3, Phase 6
  └── Qdrant/learning
  └── Interactive enhancement
```

---

## Dependencies

- Phase 2 depends on Phase 1 (schema must exist first)
- Phase 3 depends on Phase 1 (needs engagement structure)
- Phase 4 depends on Phase 1 + 2 (needs data)
- Phase 5+ can proceed in parallel after Phase 4

---

## Success Criteria

- [ ] All December 2025 resume content in database
- [ ] Engagements properly structured for BBC roles
- [ ] DOCX output matches new resume format
- [ ] Skills section uses category grouping
- [ ] ATS score calculated for generated resumes
- [ ] Resume critic validates output quality

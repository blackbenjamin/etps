# ETPS Resume Schema – v1.3.0  
**Unified Specification for Resume Storage, Transformation, Matching & Rendering**  
**Benjamin Black / ETPS – December 2025**

This document merges:
- The original ETPS schema update requirements, and  
- The full implementation-ready v1.3.0 schema specification  

This is the **master configuration file** for Claude Code and defines all structures, rules, and logic for:

- Résumé storage  
- Role → engagement → bullet hierarchy  
- JD parsing and mapping  
- Resume tailoring  
- DOCX formatting preservation  
- Critic evaluations  
- ATS scoring  
- Summary + tone rules  
- LinkedIn optimization  

This file is the **authoritative, single source of truth** for the Enterprise-Grade Talent Positioning System (ETPS).

---

# ============================================================
# 0. Scope & Goals
# ============================================================

- **Scope:** Single-user (Benjamin Black) but forward-compatible with multi-user expansion.  
- **Purpose:**  
  Build a system that can:  
  - Parse & store structured resume data  
  - Generate tailored resumes + cover letters  
  - Preserve DOCX formatting  
  - Provide critic-driven improvement loops  
  - Evaluate ATS / JD / role alignment  
  - Leverage structured metadata for precision output  

---

# ============================================================
# 1. Core Professional Identity Fields
# ============================================================

## 1.1 Original Requested Updates (Merged)
Your resume now positions you as:

- **primary_identity:** "AI & Data Leader"
- **specializations:**
  - AI Strategy  
  - Enterprise AI Systems Development  
  - Data Governance & Architecture  
  - Financial Services Data & Analytics  
  - AI Risk & Evaluation  

## 1.2 Final Schema Representation

```jsonc
candidate_profile: {
  "full_name": "Benjamin Black",
  "email_primary": "ben@benjaminblack.consulting",
  "phone": "+1-617-504-5529",
  "location": "Boston, MA, USA",
  "linkedin_url": "https://www.linkedin.com/in/benjaminblack",
  "portfolio_url": "https://projects.benjaminblack.consulting",

  "primary_identity": "AI & Data Leader",
  "specializations": [
    "AI Strategy",
    "AI Enablement",
    "Enterprise AI Systems Development",
    "Data Governance & Architecture",
    "Financial Services AI",
    "AI Risk & Evaluation"
  ],

  "seniority_level": "Senior / Principal",
  "ai_systems_builder": true,

  "target_roles": [
    "AI Strategist",
    "AI Enablement Lead",
    "Director of Data & AI",
    "AI Platform Lead",
    "Head of AI Governance & Enablement"
  ],

  "schema_version": "1.3.0"
}
============================================================
2. Skills Schema
============================================================
2.1 Original Updates (Merged)
New skills include:

RAG

LLM Evaluation

Embeddings & Vector Search

AI Governance

Enterprise Data Architecture

Zero-Trust Foundations

Cloud Platforms

Analytics Modernization

2.2 Final Schema
Each skill includes:

name

category

level (expert/advanced/intermediate/basic)

core (true/false)

jsonc
Copy code
skills: [
  { "name": "RAG (Retrieval-Augmented Generation)", "category": "AI/ML", "level": "advanced", "core": true },
  { "name": "LLM Evaluation", "category": "AI/ML", "level": "advanced", "core": true },
  { "name": "Embeddings & Vector Search", "category": "AI/ML", "level": "advanced", "core": true },
  { "name": "Prompt Engineering", "category": "AI/ML", "level": "advanced", "core": true },
  { "name": "AI Governance", "category": "Governance", "level": "advanced", "core": true },
  { "name": "Data Governance", "category": "Governance", "level": "advanced", "core": true },
  { "name": "Enterprise Data Architecture", "category": "Architecture", "level": "advanced", "core": true },
  { "name": "SQL", "category": "Tech", "level": "advanced", "core": true },
  { "name": "Python", "category": "Tech", "level": "advanced", "core": true },
  { "name": "Spark", "category": "Tech", "level": "intermediate", "core": false },
  { "name": "Azure", "category": "Cloud", "level": "advanced", "core": true },
  { "name": "AWS", "category": "Cloud", "level": "advanced", "core": true },
  { "name": "GCP", "category": "Cloud", "level": "intermediate", "core": false },
  { "name": "Analytics Modernization", "category": "Analytics", "level": "advanced", "core": true },
  { "name": "Zero-Trust Foundations", "category": "Security", "level": "intermediate", "core": false }
]
============================================================
3. Employment History Schema
============================================================
Your original file requested:

New roles

AI-specific metadata

FS-relevance scoring

Tools/technologies lists

These are now fully integrated into the v1.3.0 employment schema.

3.1 Final Employment Object Structure
jsonc
Copy code
employment_history: [
  {
    "employer": "Benjamin Black Consulting",
    "employer_type": "independent_consulting",
    "location": "Boston, MA",
    "role_title": "Independent AI Strategist & Builder",
    "start_date": "2025-10",
    "end_date": null,

    "role_summary": "Designing and delivering enterprise-grade AI systems, portfolio projects, and advisory assets.",

    "ai_systems_built": ["ETPS", "RAG systems", "AI governance dashboards"],
    "governance_frameworks_created": ["AI readiness model"],
    "fs_domain_relevance": 0.9,
    "tools_and_technologies": ["Claude", "Vector DBs", "Python", "Next.js", "DOCX generation"],

    "engagements": [
      {
        "client": null,
        "project_name": "Enterprise-Grade Talent Positioning System (ETPS)",
        "project_type": "product_build",
        "date_range_label": "2025 – Present",
        "domain_tags": ["AI Strategy", "LLM Systems", "ATS", "Career Tools"],
        "tech_tags": ["Claude", "Multi-Agent", "RAG", "Vector DB"],
        "bullets": [
          {
            "text": "Building a multi-agent Enterprise-Grade Talent Positioning System with critic loops, adaptive resume tailoring, cover-letter generation, and docx-preserving formatting.",
            "importance": "high",
            "tags": ["ATS", "AI Systems"],
            "ai_first_choice": true
          }
        ]
      }
    ]
  }
]
All other roles follow this same pattern.
============================================================
4. AI Portfolio Schema
============================================================
Your original requirements requested categories + tech stack.

Final schema:

jsonc
Copy code
ai_portfolio: [
  {
    "project_name": "RAG Research Assistant",
    "project_type": "RAG System",
    "tech_stack": ["Python", "Claude", "Vector DB"],
    "fs_relevance": true,
    "repeatable_asset": true,
    "link_to_portfolio": "https://projects.benjaminblack.consulting"
  }
]
============================================================
5. Domain Expertise Tag Schema
============================================================
Merging your tags + v1.3.0 vocabulary:

jsonc
Copy code
domain_tags_master: [
  "Financial Services",
  "Broker-Dealer",
  "Asset Management",
  "Banking",
  "WealthTech",
  "Core Banking Integration",
  "Regulatory Compliance",
  "SEC Modernization",
  "AI Strategy",
  "AI Governance",
  "Data Governance",
  "Data Architecture",
  "Analytics Modernization",
  "Cloud Platforms",
  "DoD / Defense",
  "Kessel Run",
  "Enterprise Transformations"
]
============================================================
6. Education Schema
============================================================
Your previous request added:

executive_credibility_score

language fluency

Final schema:

jsonc
Copy code
education: [
  {
    "institution": "MIT Sloan School of Management",
    "degree": "MBA",
    "fields": ["Strategy", "Finance", "Innovation"],
    "graduation_year": 2014,
    "prestige_weight": 0.95,
    "executive_credibility_score": 1.0
  },
  {
    "institution": "Tufts University",
    "degree": "B.A.",
    "fields": ["Economics", "International Relations", "German Studies"],
    "language_fluency": ["German"],
    "prestige_weight": 0.75
  }
]
============================================================
7. Summary Schema Block (Merged)
============================================================
Your original file wanted:

positioning statement

value proposition

capabilities

Final unified schema:

jsonc
Copy code
summary: {
  "text": "AI and data strategist with deep experience building enterprise-grade AI systems, leading data governance and analytics modernization, and driving cross-functional transformation across financial services and government. Known for delivering scalable platforms and aligning diverse teams around meaningful outcomes. MIT Sloan MBA.",
  "max_words": 60,
  "tone": "executive_direct_concise",
  "required_elements": [
    "AI systems leadership",
    "Data/analytics modernization",
    "Governance expertise",
    "Cross-functional delivery"
  ],
  "banned_phrases": [
    "I am writing to express my interest",
    "Passionate",
    "Dynamic professional",
    "I believe I would be a great fit",
    "Per your job description"
  ]
}
============================================================
8. JD Matching & Role Fit Logic
============================================================
Your original fields now fully integrated:

8.1 JD Parsing
jsonc
Copy code
job_profile: {
  "title": "",
  "company": "",
  "location": "",
  "seniority_level": "",
  "industry": "",
  "core_requirements": [],
  "responsibilities": [],
  "keywords": [],
  "ai_maturity_signals": []
}
8.2 Match Scoring
jsonc
Copy code
match_result: {
  "overall_score": 0.0,
  "skills_score": 0.0,
  "domain_score": 0.0,
  "seniority_score": 0.0,
  "gaps": [],
  "reasoning": ""
}
8.3 Role Classification Flags
jsonc
Copy code
role_classification: {
  "match_ai_strategy_roles": false,
  "match_director_data_ai_roles": false,
  "match_ai_architect_roles": false,
  "match_engagement_manager_roles": false,

  "exclude_full_time_engineer_roles": true,
  "exclude_research_scientist_roles": true
}
============================================================
9. LinkedIn Optimization Metadata
============================================================
jsonc
Copy code
linkedin_meta: {
  "headline_recommended": "AI & Data Strategist | Building Enterprise AI Systems, Data Governance & Analytics Platforms | MIT Sloan MBA",
  "about_section_current": null,
  "top_skills_selected": [
    "AI Strategy",
    "Data Governance",
    "Analytics Modernization"
  ],
  "open_to_work_titles": [
    "Director of Data & AI",
    "AI Strategist",
    "Head of AI Enablement"
  ]
}
============================================================
10. Resume Formatting Schema (DOCX-Preservation)
============================================================
Section Order
Header

Summary

Experience

Skills

Education

Header Rules
Name: ALL CAPS, bold

Contact line centered

Portfolio line centered, 0.5pt smaller allowed

Experience Rules
Employers sorted newest → oldest

For multi-page employers, repeat employer + title + dates with optional (continued)

Consulting roles show client subheadings

Dates right-aligned

Bullet Rules
Bullet = ●

Strong verb first

Max 2 lines

No em-dashes

No first-person

No fluff phrases

============================================================
11. Resume Critic Schema
============================================================
jsonc
Copy code
resume_critic_result: {
  "formatting_ok": true,
  "formatting_issues": [],
  "tone_ok": true,
  "tone_issues": [],
  "truthfulness_ok": true,
  "truthfulness_issues": [],

  "ats_score_estimate": 0.0,
  "banned_phrases_found": [],

  "alignment_notes": [],
  "revision_suggestions": []
}
Rules:

Critic must be strict

Resume is "ready" only when no issues remain

============================================================
12. Versioning & Migration Notes
============================================================
Your original versioning request is fully integrated:

Schema version now: v1.3.0

Migrates from v1.2.0

Adds AI-first identity, new employment, bullet rules, ATS structures, critic schema, JD parser schema.

End of Document
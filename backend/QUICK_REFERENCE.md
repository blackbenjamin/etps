# ETPS Quick Reference Guide

## Import Statements

```python
# Text Processing
from utils.text_processing import fetch_url_content, clean_text, extract_bullets

# LLM Services
from services.llm import BaseLLM, MockLLM

# Schemas - Job Parser
from schemas import (
    JobParseRequest,
    JobParseResponse,
    JobProfileDTO
)

# Schemas - Skill Gap
from schemas import (
    UserSkillProfile,
    SkillMatch,
    SkillGap,
    WeakSignal,
    SkillGapRequest,
    SkillGapResponse
)

# All at once
from schemas import *
```

## Text Processing Examples

```python
# Fetch and clean URL content
content = fetch_url_content("https://example.com/job-posting")

# Clean messy text
clean = clean_text("""
Multiple    spaces    and


too   many   newlines
""")
# Result: "Multiple spaces and\n\ntoo many newlines"

# Extract bullet points
bullets = extract_bullets("""
Responsibilities:
- Lead AI initiatives
* Develop frameworks
• Manage stakeholders
1. Conduct assessments
2. Provide guidance
""")
# Result: ['Lead AI initiatives', 'Develop frameworks', 'Manage stakeholders', ...]
```

## Mock LLM Examples

```python
import asyncio
from services.llm import MockLLM

llm = MockLLM()

# Generate core priorities
priorities = await llm.generate_core_priorities(
    jd_text="Job description text...",
    context={}
)
# Returns: List of 3-5 priority strings

# Infer tone
tone = await llm.infer_tone("Job description text...")
# Returns: 'mission_driven' | 'startup_casual' | 'formal_corporate' | etc.

# General text generation
response = await llm.generate_text("Prompt text...", max_tokens=500)
```

## Schema Examples

### Job Parse Request

```python
# With text
request = JobParseRequest(
    jd_text="Full job description text...",
    user_id=1
)

# With URL
request = JobParseRequest(
    jd_url="https://example.com/job",
    user_id=1
)

# Invalid: both provided (raises ValueError)
request = JobParseRequest(
    jd_text="text",
    jd_url="url",
    user_id=1
)

# Invalid: neither provided (raises ValueError)
request = JobParseRequest(user_id=1)
```

### Job Parse Response

```python
from datetime import datetime

response = JobParseResponse(
    job_profile_id=123,
    raw_jd_text="Original JD text...",
    jd_url="https://example.com/job",
    job_title="Senior AI Consultant",
    company_name="Acme Corp",
    location="San Francisco, CA",
    seniority="senior",
    responsibilities="Lead AI initiatives...",
    requirements="5+ years experience...",
    nice_to_haves="PhD in CS...",
    extracted_skills=["Python", "AI/ML", "Consulting"],
    core_priorities=[
        "AI governance framework development",
        "Stakeholder management",
        "Technical oversight"
    ],
    must_have_capabilities=["Framework Development", "Leadership"],
    nice_to_have_capabilities=["Research Background"],
    tone_style="consulting_professional",
    job_type_tags=["ai_governance", "consulting"],
    created_at=datetime.now().isoformat()
)
```

### User Skill Profile

```python
profile = UserSkillProfile(
    skills=["Python", "Machine Learning", "AI Governance"],
    capabilities=["Strategic Planning", "Team Leadership"],
    bullet_tags=["ai", "governance", "consulting", "leadership"],
    seniority_levels=["senior", "director"],
    relevance_scores={
        "ai": 0.92,
        "governance": 0.88,
        "consulting": 0.75
    }
)
```

### Skill Match

```python
match = SkillMatch(
    skill="Python Programming",
    match_strength=0.95,  # 0.0 to 1.0
    evidence=[
        "5 years Python experience",
        "Led ML project in Python",
        "Open source contributions"
    ]
)
```

### Skill Gap

```python
gap = SkillGap(
    skill="Kubernetes",
    importance="important",  # 'critical' | 'important' | 'nice-to-have'
    positioning_strategy="Emphasize Docker expertise and quick learning ability"
)

# Auto-converts importance to lowercase
gap = SkillGap(
    skill="Test",
    importance="CRITICAL",  # Converted to 'critical'
    positioning_strategy="..."
)
```

### Weak Signal

```python
weak = WeakSignal(
    skill="Product Management",
    current_evidence=[
        "Led cross-functional initiatives",
        "Gathered stakeholder requirements"
    ],
    strengthening_strategy="Frame technical leadership through product lens"
)
```

### Skill Gap Request

```python
# With explicit user profile
request = SkillGapRequest(
    job_profile_id=123,
    user_id=1,
    user_skill_profile=UserSkillProfile(
        skills=["Python", "AI"],
        capabilities=["Leadership"],
        bullet_tags=["ai", "leadership"],
        seniority_levels=["senior"],
        relevance_scores={"ai": 0.9}
    )
)

# Without explicit profile (will be derived from user data)
request = SkillGapRequest(
    job_profile_id=123,
    user_id=1
)
```

### Skill Gap Response

```python
from datetime import datetime

response = SkillGapResponse(
    job_profile_id=123,
    user_id=1,
    skill_match_score=85.5,  # 0-100
    recommendation="strong_match",  # 'strong_match' | 'moderate_match' | 'weak_match' | 'stretch_role'
    confidence=0.88,  # 0.0-1.0
    matched_skills=[
        SkillMatch(
            skill="Python",
            match_strength=0.95,
            evidence=["5 years experience"]
        )
    ],
    skill_gaps=[
        SkillGap(
            skill="Kubernetes",
            importance="important",
            positioning_strategy="..."
        )
    ],
    weak_signals=[
        WeakSignal(
            skill="Product Management",
            current_evidence=["..."],
            strengthening_strategy="..."
        )
    ],
    key_positioning_angles=[
        "Technical AI expertise with governance focus",
        "Proven track record in enterprise consulting",
        "Strong leadership and stakeholder management"
    ],
    bullet_selection_guidance={
        "high_priority": ["ai_governance", "consulting", "leadership"],
        "medium_priority": ["technical", "strategy"],
        "emphasize": ["impact_metrics", "stakeholder_work"]
    },
    cover_letter_hooks=[
        "Passion for responsible AI development",
        "Track record building governance frameworks",
        "Experience bridging technical and business stakeholders"
    ],
    user_advantages=[
        "Unique combination of technical depth and strategic thinking",
        "Proven ability to influence senior stakeholders"
    ],
    potential_concerns=[
        "Limited direct consulting firm experience",
        "No specific industry certifications"
    ],
    mitigation_strategies={
        "consulting_experience": "Highlight embedded consulting roles with Fortune 500 clients",
        "certifications": "Emphasize practical hands-on experience over credentials"
    },
    analysis_timestamp=datetime.now().isoformat()
)
```

## Common Patterns

### Job Parsing Flow

```python
from utils.text_processing import fetch_url_content, clean_text, extract_bullets
from services.llm import MockLLM
from schemas import JobParseRequest, JobParseResponse

async def parse_job(url: str, user_id: int):
    # 1. Fetch content
    raw_text = fetch_url_content(url)

    # 2. Clean text
    cleaned = clean_text(raw_text)

    # 3. Extract bullets
    bullets = extract_bullets(cleaned)

    # 4. Analyze with LLM
    llm = MockLLM()
    priorities = await llm.generate_core_priorities(cleaned, {})
    tone = await llm.infer_tone(cleaned)

    # 5. Create response
    response = JobParseResponse(
        job_profile_id=123,  # From database
        raw_jd_text=cleaned,
        jd_url=url,
        job_title="Extracted Title",
        core_priorities=priorities,
        tone_style=tone,
        # ... other fields
        created_at=datetime.now().isoformat()
    )

    return response
```

### Skill Gap Analysis Flow

```python
from schemas import SkillGapRequest, SkillGapResponse, SkillMatch, SkillGap

async def analyze_skill_gap(job_profile_id: int, user_id: int):
    # 1. Create request
    request = SkillGapRequest(
        job_profile_id=job_profile_id,
        user_id=user_id
    )

    # 2. Load user data and job profile from database
    # user_data = load_user_bullets_and_skills(user_id)
    # job_profile = load_job_profile(job_profile_id)

    # 3. Perform matching and gap analysis
    # matched_skills = match_skills(user_data, job_profile)
    # gaps = identify_gaps(user_data, job_profile)

    # 4. Create response
    response = SkillGapResponse(
        job_profile_id=job_profile_id,
        user_id=user_id,
        skill_match_score=82.5,
        recommendation="strong_match",
        confidence=0.85,
        matched_skills=[...],
        skill_gaps=[...],
        # ... other fields
        analysis_timestamp=datetime.now().isoformat()
    )

    return response
```

## Validation Error Handling

```python
from pydantic import ValidationError

try:
    request = JobParseRequest(user_id=1)  # Missing jd_text/jd_url
except ValidationError as e:
    print(e)
    # Shows: "Must provide either jd_text or jd_url"

try:
    gap = SkillGap(
        skill="Test",
        importance="invalid_level",
        positioning_strategy="..."
    )
except ValidationError as e:
    print(e)
    # Shows: "importance must be one of ['critical', 'important', 'nice-to-have']"
```

## Testing

```bash
# Run all tests
python3 test_implementation.py

# Quick import test
python3 -c "from utils.text_processing import *; from services.llm import *; from schemas import *; print('✓ All imports successful')"

# Test MockLLM
python3 -c "
import asyncio
from services.llm import MockLLM

async def test():
    llm = MockLLM()
    priorities = await llm.generate_core_priorities('AI governance consulting role...', {})
    print('Priorities:', priorities)

asyncio.run(test())
"
```

## File Locations

```
/Users/benjaminblack/projects/recruitbot/backend/
├── utils/
│   ├── __init__.py
│   └── text_processing.py
├── services/llm/
│   ├── __init__.py
│   ├── base.py
│   └── mock_llm.py
├── schemas/
│   ├── __init__.py
│   ├── job_parser.py
│   └── skill_gap.py
└── test_implementation.py
```

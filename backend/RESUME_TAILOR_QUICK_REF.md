# Resume Tailoring Service - Quick Reference

## Main Function

```python
from services.resume_tailor import tailor_resume
from services.llm.mock_llm import MockLLM

result = await tailor_resume(
    job_profile_id=123,      # Required: Target job profile ID
    user_id=456,              # Required: User ID
    db=db_session,            # Required: SQLAlchemy session
    max_bullets_per_role=4,   # Optional: 2-8 bullets per role (default: 4)
    max_skills=12,            # Optional: 5-20 skills total (default: 12)
    custom_instructions=None, # Optional: User instructions (not yet implemented)
    llm=MockLLM(),           # Optional: LLM instance (defaults to MockLLM)
)
```

## Response Structure

```python
TailoredResume(
    job_profile_id=123,
    user_id=456,
    application_id=None,                    # Link to application if created
    tailored_summary="Leader with 6+ years...",  # 60-80 words
    selected_roles=[                        # List of SelectedRole
        SelectedRole(
            experience_id=1,
            job_title="Senior Consultant",  # IMMUTABLE
            employer_name="Acme Corp",      # IMMUTABLE
            location="NYC",                  # IMMUTABLE
            start_date="2021-01-01",
            end_date=None,
            selected_bullets=[               # List of SelectedBullet
                SelectedBullet(
                    bullet_id=10,
                    text="Led AI governance initiatives...",
                    relevance_score=0.85,
                    was_rewritten=False,
                    tags=["ai_governance", "consulting"],
                    selection_reason="Matches key skills: ai_governance..."
                )
            ],
            bullet_selection_rationale="Selected 4 bullets emphasizing..."
        )
    ],
    selected_skills=[                       # List of SelectedSkill
        SelectedSkill(
            skill="AI Governance",
            priority_score=0.95,
            match_type="direct_match",      # or "adjacent_skill", "transferable"
            source="job_requirements"       # or "user_master_resume"
        )
    ],
    rationale=TailoringRationale(
        summary_approach="Generated summary emphasizing...",
        bullet_selection_strategy="Multi-factor scoring...",
        skills_ordering_logic="Tier-based selection...",
        role_emphasis={1: "Current role (high priority)"},
        gaps_addressed=["Policy Development (important): ..."],
        strengths_highlighted=["AI Governance (strength: 0.95)"]
    ),
    ats_score_estimate=None,               # Not yet implemented
    match_score=85.3,                       # 0-100 overall match quality
    generated_at="2024-12-04T12:00:00",
    constraints_validated=True              # All immutable fields preserved
)
```

## Helper Functions

### Select Bullets for Single Role

```python
from services.resume_tailor import select_bullets_for_role

selected_bullets = select_bullets_for_role(
    experience=experience_obj,        # Experience ORM model
    bullets=list_of_bullets,          # List[Bullet] for this experience
    job_profile=job_profile_obj,      # JobProfile ORM model
    skill_gap_result=skill_gap_resp,  # SkillGapResponse from skill_gap service
    max_bullets=4                     # Max bullets to select
)
# Returns: List[SelectedBullet]
```

### Select and Order Skills

```python
from services.resume_tailor import select_and_order_skills

selected_skills = select_and_order_skills(
    user_bullets=all_user_bullets,    # List[Bullet] for user
    job_profile=job_profile_obj,      # JobProfile ORM model
    skill_gap_result=skill_gap_resp,  # SkillGapResponse
    max_skills=12                     # Max skills to include
)
# Returns: List[SelectedSkill]
```

### Generate Tailored Summary

```python
from services.resume_tailor import generate_tailored_summary
from services.llm.mock_llm import MockLLM

summary = await generate_tailored_summary(
    user_name="Jane Smith",
    experiences=list_of_experiences,   # List[Experience]
    job_profile=job_profile_obj,       # JobProfile
    skill_gap_result=skill_gap_resp,   # SkillGapResponse
    selected_skills=selected_skills,   # List[SelectedSkill]
    llm=MockLLM()                      # BaseLLM instance
)
# Returns: str (60-80 words)
```

## Scoring Algorithms

### Bullet Selection Scoring (0.0-1.0)
- **40%**: Tag matching against job skills (with synonym support)
- **30%**: Pre-computed relevance scores
- **20%**: Usage/recency (prefer less-used bullets)
- **10%**: Type diversity (achievement/metric_impact bonus)

### Skill Selection Tiers
1. **Tier 1**: Critical matches (match_strength >= 0.75)
2. **Tier 2**: Strong matches (0.5 <= match_strength < 0.75)
3. **Tier 3**: Must-have job requirements
4. **Tier 4**: Weak signals and transferable skills

### Match Score Calculation (0-100)
- Base: Skill gap analysis score
- +5 bonus: Sufficient bullet count (≥8 total)
- +3 bonus: Good skill coverage (≥80% of max)
- Capped at 100.0

## Constants

### Banned Phrases (Auto-removed from summaries)
```python
BANNED_PHRASES = [
    "seasoned professional", "results-oriented", "proven track record",
    "dynamic", "synergy", "leverage", "best-in-class", "world-class",
    "cutting-edge", "innovative thinker", "go-getter", "team player",
    "detail-oriented", "hard-working", "passionate about"
]
```

### Bullet Types
- `achievement`: Major accomplishment or project
- `responsibility`: Key duty or role function
- `metric_impact`: Quantified business impact
- `general`: Unclassified bullet

### Match Types
- `direct_match`: Exact skill match (high confidence)
- `adjacent_skill`: Related or complementary skill
- `transferable`: Applicable skill from different domain

## Error Handling

```python
try:
    result = await tailor_resume(...)
except ValueError as e:
    # Raised for:
    # - Job profile not found
    # - User not found
    # - No experiences for user
    # - Invalid parameter ranges
    print(f"Error: {e}")
```

## Testing

Run test suite:
```bash
python test_resume_tailor.py
```

Expected output:
```
======================================================================
RESUME TAILORING SERVICE TEST SUITE
======================================================================

✓ TEST: select_bullets_for_role()
✓ TEST: select_and_order_skills()
✓ TEST: generate_tailored_summary()
✓ TEST: tailor_resume() - Full Integration

ALL TESTS COMPLETED SUCCESSFULLY
```

## Common Use Cases

### 1. Generate Resume for Job Application
```python
# User applies to job - generate tailored resume
result = await tailor_resume(
    job_profile_id=job.id,
    user_id=current_user.id,
    db=db,
    max_bullets_per_role=4,
    max_skills=12
)

# Save to application record
application.resume_json = result.dict()
application.ats_score = result.match_score
db.commit()
```

### 2. Preview Different Configurations
```python
# Show user different resume lengths
short = await tailor_resume(..., max_bullets_per_role=3, max_skills=8)
medium = await tailor_resume(..., max_bullets_per_role=4, max_skills=12)
long = await tailor_resume(..., max_bullets_per_role=5, max_skills=15)

# Let user choose preferred version
```

### 3. Analyze Resume Quality
```python
result = await tailor_resume(...)

print(f"Match Score: {result.match_score}/100")
print(f"Strengths: {', '.join(result.rationale.strengths_highlighted[:3])}")
print(f"Gaps: {', '.join(result.rationale.gaps_addressed[:3])}")

if result.match_score < 60:
    print("Warning: Low match score - consider different role")
```

### 4. Audit Bullet Usage
```python
result = await tailor_resume(...)

for role in result.selected_roles:
    print(f"\n{role.job_title}:")
    for bullet in role.selected_bullets:
        print(f"  [{bullet.relevance_score:.2f}] {bullet.text[:60]}...")
        print(f"  Reason: {bullet.selection_reason}")
```

## Performance Tips

1. **Reuse skill_gap results**: If analyzing same job multiple times
2. **Batch process**: Generate resumes for multiple jobs in parallel
3. **Cache LLM responses**: Store summary templates by job type
4. **Index bullets**: Ensure tags and relevance_scores are indexed
5. **Limit experiences**: Consider excluding very old experiences

## Constraints (PRD Requirements)

**IMMUTABLE FIELDS** - Never modified:
- `job_title`
- `employer_name`
- `location`
- `start_date`
- `end_date`

**VALIDATION RULES**:
- 2-8 bullets per role
- 5-20 total skills
- All selected content from user's master resume
- No fabricated or hallucinated content
- `constraints_validated` flag must be True

## Integration with Other Services

```python
# 1. Parse job description
from services.job_parser import parse_job_description
job_profile = await parse_job_description(jd_text, user_id, db)

# 2. Analyze skill gap
from services.skill_gap import analyze_skill_gap
skill_gap = await analyze_skill_gap(job_profile.id, user_id, db)

# 3. Tailor resume
from services.resume_tailor import tailor_resume
resume = await tailor_resume(job_profile.id, user_id, db)

# 4. Generate document
from services.docx_generator import generate_docx  # Future
docx_path = await generate_docx(resume, template_id)
```

## Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

result = await tailor_resume(...)

# Check rationale for decisions
print(result.rationale.bullet_selection_strategy)
print(result.rationale.skills_ordering_logic)

# Verify constraints
assert result.constraints_validated, "Constraint violation!"
```

## Known Limitations

1. **No bullet rewriting**: `was_rewritten` always False (future feature)
2. **No ATS scoring**: `ats_score_estimate` always None (future feature)
3. **No custom instructions**: Parameter accepted but not processed yet
4. **Mock LLM only**: Real LLM integration pending
5. **English only**: No i18n support yet

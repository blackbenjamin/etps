# ETPS Backend Testing Plan

**Version:** 1.0
**Created:** December 2024
**Purpose:** Pre-deployment validation of all ETPS backend capabilities

---

## Prerequisites

### 1. Environment Setup
```bash
cd /Users/benjaminblack/projects/etps/backend
source venv/bin/activate  # or your virtual environment
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Initialize SQLite database (if not exists)
python -c "from db.database import engine; from db.models import Base; Base.metadata.create_all(bind=engine)"
```

### 3. Start the Server
```bash
uvicorn main:app --reload --port 8000
```

### 4. API Testing Tools
- **Swagger UI**: http://localhost:8000/docs
- **cURL** or **httpie** for command-line testing
- **Postman** (optional) for saved test collections

---

## Test Categories

1. [Portfolio Loader Service](#1-portfolio-loader-service)
2. [Job Profile Extraction](#2-job-profile-extraction)
3. [Skill Gap Analysis](#3-skill-gap-analysis)
4. [Cover Letter Generation](#4-cover-letter-generation)
5. [Style Guide Compliance](#5-style-guide-compliance)
6. [Critic Evaluation](#6-critic-evaluation)
7. [Cover Letter DOCX Generation](#7-cover-letter-docx-generation)
8. [Resume Tailoring](#8-resume-tailoring)
9. [Resume DOCX Generation](#9-resume-docx-generation)

---

## 1. Portfolio Loader Service

### Test 1.1: Load User Portfolio
```python
python -c "
from services.portfolio_loader import load_user_portfolio
portfolio = load_user_portfolio()
print(f'User: {portfolio[\"user\"][\"full_name\"]}')
print(f'Experiences: {len(portfolio[\"experiences\"])}')
print(f'Education: {len(portfolio[\"education\"])}')
"
```

**Expected:**
- User name: "Benjamin Black"
- Multiple experiences loaded
- Education entries present

### Test 1.2: Get All Bullets
```python
python -c "
from services.portfolio_loader import get_all_bullets
bullets = get_all_bullets()
print(f'Total bullets: {len(bullets)}')
print(f'Sample bullet: {bullets[0][\"text\"][:80]}...')
"
```

**Expected:**
- 25+ bullets loaded
- Each bullet has text, tags, seniority_level, bullet_type

### Test 1.3: Filter Bullets by Tags
```python
python -c "
from services.portfolio_loader import get_bullets_by_tags
bullets = get_bullets_by_tags(['data_governance', 'consulting'])
print(f'Matching bullets: {len(bullets)}')
for b in bullets[:3]:
    print(f'  - {b[\"text\"][:60]}...')
"
```

**Expected:**
- Returns bullets matching specified tags
- Tags visible in bullet metadata

### Test 1.4: Get Skills by Category
```python
python -c "
from services.portfolio_loader import get_all_skills
skills = get_all_skills()
for category, skill_list in skills.items():
    print(f'{category}: {len(skill_list)} skills')
"
```

**Expected:**
- Categories: ai_ml, data, tech, bi, tools
- Multiple skills per category

---

## 2. Job Profile Extraction

### Test 2.1: Create Job Profile via API
```bash
curl -X POST "http://localhost:8000/job-profile/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Senior Data Scientist at Acme Corp. Requirements: 5+ years Python, machine learning, SQL. Must have experience with cloud platforms (AWS/GCP). Nice to have: RAG systems, LLM fine-tuning.",
    "source_url": "https://example.com/job/123"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "job_title": "Senior Data Scientist",
  "employer_name": "Acme Corp",
  "extracted_skills": ["Python", "machine learning", "SQL", "AWS", "GCP"],
  "must_have_capabilities": ["5+ years Python", "machine learning", "SQL"],
  "nice_to_have_capabilities": ["RAG systems", "LLM fine-tuning"],
  "tone_style": "formal_corporate"
}
```

### Test 2.2: Retrieve Job Profile
```bash
curl "http://localhost:8000/job-profile/1"
```

**Expected:** Returns the created job profile with all fields

---

## 3. Skill Gap Analysis

### Test 3.1: Analyze Skill Gap
```bash
curl -X POST "http://localhost:8000/skill-gap/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "job_profile_id": 1,
    "user_id": 1
  }'
```

**Expected Response:**
```json
{
  "matched_skills": [...],
  "weak_signals": [...],
  "user_advantages": [...],
  "recommendation": "strong_match" | "moderate_match" | "stretch_role",
  "cover_letter_hooks": [...]
}
```

**Verify:**
- Matched skills have match_strength scores
- Weak signals identify gaps
- Cover letter hooks are actionable suggestions

---

## 4. Cover Letter Generation

### Test 4.1: Generate Cover Letter (JSON)
```bash
curl -X POST "http://localhost:8000/cover-letter/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "job_profile_id": 1,
    "user_id": 1,
    "company_profile_id": null,
    "context_notes": "Emphasize AI governance experience"
  }'
```

**Expected Response Fields:**
- `draft_cover_letter`: Full text (250-350 words)
- `outline`: Object with introduction, value_proposition, alignment, call_to_action
- `banned_phrase_check`: Object with violations_found, passed
- `tone_compliance`: Object with compliance_score, compatible
- `ats_keyword_coverage`: Object with coverage_percentage, covered_keywords
- `requirements_covered`: Array of top 2-3 JD requirements
- `quality_score`: Number 0-100

### Test 4.2: Generate with Critic Evaluation
```bash
curl -X POST "http://localhost:8000/cover-letter/generate-with-critic" \
  -H "Content-Type: application/json" \
  -d '{
    "job_profile_id": 1,
    "user_id": 1
  }'
```

**Expected Response:**
```json
{
  "cover_letter": { ... },
  "critic_result": {
    "passed": true|false,
    "issues": [...],
    "error_count": 0,
    "warning_count": 0,
    "em_dash_count": 0,
    "requirement_coverage": { ... }
  },
  "accepted": true|false
}
```

---

## 5. Style Guide Compliance

### Test 5.1: Banned Phrase Detection
```python
python -c "
from services.cover_letter import check_banned_phrases

# Test with banned phrases
text = '''
I am writing to express my interest in the Data Scientist role.
I believe I would be a great fit for this position.
I look forward to hearing from you.
'''
result = check_banned_phrases(text)
print(f'Violations: {result.violations_found}')
print(f'Passed: {result.passed}')
print(f'Severity: {result.overall_severity}')
for v in result.violations:
    print(f'  - \"{v.phrase}\" ({v.severity})')
"
```

**Expected:**
- 3 violations detected
- passed: False
- overall_severity: critical

### Test 5.2: Em-Dash Detection
```python
python -c "
from services.cover_letter import check_em_dashes

# Test with em-dashes (should fail)
text = 'My experience—spanning multiple domains—is relevant.'
violations = check_em_dashes(text)
print(f'Em-dash violations: {len(violations)}')

# Test with hyphens (should pass)
text2 = 'This is a well-known, state-of-the-art solution.'
violations2 = check_em_dashes(text2)
print(f'Hyphen false positives: {len(violations2)}')
"
```

**Expected:**
- Em-dash test: 2 violations
- Hyphen test: 0 violations (no false positives)

### Test 5.3: Clean Cover Letter
```python
python -c "
from services.cover_letter import check_banned_phrases

# Clean cover letter text
text = '''
I am applying for the Senior Data Scientist role at Acme Corp.
My background spans data strategy, AI enablement, and investment-domain
transformation across asset management and defense.

At Kessel Run, I supported the CIO/CDO by leading research on AI governance
and data architectures. This experience directly aligns with your requirements.

I would welcome the opportunity to discuss how my background can contribute
to Acme's goals.
'''
result = check_banned_phrases(text)
print(f'Violations: {result.violations_found}')
print(f'Passed: {result.passed}')
"
```

**Expected:**
- violations_found: 0
- passed: True

---

## 6. Critic Evaluation

### Test 6.1: Critic on Clean Letter
```python
python -c "
import asyncio
from services.critic import check_em_dashes, check_banned_phrases

text = '''
I am applying for the Data Scientist role at Acme Corp.
My experience in machine learning and data engineering positions me well.
'''

em_issues = check_em_dashes(text, context='cover_letter')
banned_issues = check_banned_phrases(text, context='cover_letter')

print(f'Em-dash issues: {len(em_issues)}')
print(f'Banned phrase issues: {len(banned_issues)}')
print('✓ Clean letter passes basic checks' if len(em_issues) == 0 and len(banned_issues) == 0 else '✗ Issues found')
"
```

### Test 6.2: Requirement Coverage Check
```python
python -c "
# This requires database setup with job_profile
# Run via API instead for full test
print('Test requirement coverage via API endpoint')
"
```

---

## 7. Cover Letter DOCX Generation

### Test 7.1: DOCX Generation (Critic Passes)
```bash
curl -X POST "http://localhost:8000/cover-letter/docx" \
  -H "Content-Type: application/json" \
  -d '{
    "job_profile_id": 1,
    "user_id": 1
  }' \
  --output test_cover_letter.docx
```

**Expected:**
- Downloads .docx file
- Open in Word/LibreOffice to verify:
  - Header: BENJAMIN BLACK (centered, bold)
  - Contact line with bullet separators
  - Date right-aligned
  - Recipient block
  - Body paragraphs with proper spacing
  - Closing: "Sincerely," + signature

### Test 7.2: DOCX Generation (Critic Fails)
```bash
# First, modify mock LLM to generate text with em-dashes
# Or test with strict_mode=true on a letter with warnings

curl -X POST "http://localhost:8000/cover-letter/docx?strict_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "job_profile_id": 1,
    "user_id": 1
  }'
```

**Expected (if critic fails):**
```json
{
  "accepted": false,
  "message": "Cover letter failed critic evaluation...",
  "critic_result": { ... },
  "cover_letter": { ... }
}
```

### Test 7.3: Verify DOCX Formatting
Open the generated DOCX and check:

| Element | Expected |
|---------|----------|
| Font | Georgia throughout |
| Name | 16pt, bold, centered, UPPERCASE |
| Contact | 10.5pt, centered, bullet separators |
| Date | 11pt, right-aligned, "December 4, 2025" format |
| Recipient | Left-aligned, "Hiring Team" or custom |
| Body | ~12pt, left-aligned, proper paragraph spacing |
| Margins | Top: 0.81", Bottom: 1.0", Left: 0.5", Right: 0.56" |

---

## 8. Resume Tailoring

### Test 8.1: Tailor Resume
```bash
curl -X POST "http://localhost:8000/resume/tailor" \
  -H "Content-Type: application/json" \
  -d '{
    "job_profile_id": 1,
    "user_id": 1
  }'
```

**Expected Response:**
```json
{
  "tailored_summary": "...",
  "selected_roles": [
    {
      "experience_id": 1,
      "employer_name": "Kessel Run",
      "job_title": "...",
      "selected_bullets": [...]
    }
  ],
  "selected_skills": [...],
  "tailoring_rationale": "..."
}
```

### Test 8.2: Verify Bullet Selection
- Bullets should be relevant to job requirements
- Maximum 4 bullets per role
- Bullets sorted by relevance

---

## 9. Resume DOCX Generation

### Test 9.1: Generate Resume DOCX
```bash
curl -X POST "http://localhost:8000/resume/docx" \
  -H "Content-Type: application/json" \
  -d '{
    "job_profile_id": 1,
    "user_id": 1
  }' \
  --output test_resume.docx
```

**Expected:**
- Downloads .docx file
- Open and verify formatting matches template

---

## Regression Tests

### Before Each Deployment
Run all tests in sequence:

```bash
# 1. Service imports
python -c "
from services.portfolio_loader import load_user_portfolio
from services.cover_letter import generate_cover_letter, check_banned_phrases
from services.critic import evaluate_cover_letter
from services.docx_cover_letter import create_cover_letter_docx
from services.docx_resume import create_resume_docx
print('✓ All services import successfully')
"

# 2. Schema imports
python -c "
from schemas.cover_letter import GeneratedCoverLetter, CoverLetterRequest
from schemas.critic import CriticResult, CoverLetterCriticResult
from schemas.resume_tailor import TailoredResume
print('✓ All schemas import successfully')
"

# 3. Router imports
python -c "
from routers.cover_letter import router as cl_router
from routers.resume import router as resume_router
print(f'Cover letter routes: {[r.path for r in cl_router.routes]}')
print(f'Resume routes: {[r.path for r in resume_router.routes]}')
print('✓ All routers import successfully')
"

# 4. Syntax check all files
python -m py_compile services/cover_letter.py
python -m py_compile services/critic.py
python -m py_compile services/docx_cover_letter.py
python -m py_compile services/docx_resume.py
python -m py_compile services/portfolio_loader.py
python -m py_compile routers/cover_letter.py
python -m py_compile routers/resume.py
echo "✓ All syntax checks pass"
```

---

## Known Limitations

1. **Mock LLM**: Current implementation uses MockLLM for testing. Real LLM integration required for production.

2. **User Model**: The User model doesn't include `phone` field. Contact info in DOCX uses email only unless model is extended.

3. **Company Profile**: Company-specific customization requires a CompanyProfile entry in database.

4. **Skill Gap**: Requires job_profile.extracted_skills to be populated for accurate matching.

---

## Troubleshooting

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "User not found" | No user in database | Create user via admin or seed script |
| "Job profile not found" | Missing job profile | POST to /job-profile/parse first |
| Empty DOCX body | draft_cover_letter is empty | Check LLM generation or mock output |
| Em-dash violations | Text contains — characters | Remove em-dashes, use commas instead |
| Import errors | Missing dependencies | `pip install -r requirements.txt` |

### Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

---

## Sign-Off Checklist

Before migration:

- [ ] All service imports pass
- [ ] All schema imports pass
- [ ] All router imports pass
- [ ] Portfolio loader returns valid data
- [ ] Cover letter generation works
- [ ] Banned phrase detection works
- [ ] Em-dash detection works (no false positives on hyphens)
- [ ] Critic evaluation passes clean letters
- [ ] DOCX generation produces valid files
- [ ] DOCX formatting matches template
- [ ] API endpoints return correct status codes
- [ ] Error handling works for missing data

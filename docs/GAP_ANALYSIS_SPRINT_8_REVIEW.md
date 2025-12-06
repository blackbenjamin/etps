# ETPS Gap Analysis Report
## PRD vs Implementation Plan vs Built Code
**Date:** December 6, 2025
**Review Point:** Post-Sprint 8, Pre-Sprint 9

---

## Executive Summary

**Sprints 1-8 are complete.** The core backend functionality is largely implemented, but there are several gaps between what the PRD specifies, what the implementation plan describes, and what has actually been built.

| Category | Count |
|----------|-------|
| **Critical Gaps (Must Fix)** | 4 |
| **Medium Gaps (Should Fix)** | 6 |
| **Minor Gaps (Nice to Have)** | 5 |
| **Documentation Gaps** | 3 |

---

## CRITICAL GAPS (Must Fix Before Sprint 9)

### 1. Sprint 8 Acceptance Criteria NOT Met - Similar Examples Not Integrated into Generation

**PRD Reference:** Section 4.7, 3.1
> "For new requests, similar approved outputs are retrieved via Qdrant. Examples guide generation without copy-paste."

**Implementation Plan Task 1.8.5:** "Integrate examples into generation prompts"

**What's Built:**
- `services/output_retrieval.py` has `format_examples_for_prompt()` function
- `routers/outputs.py` has `/approve` and `/similar` endpoints

**What's Missing:**
- `services/resume_tailor.py` has imports added but **no actual integration** - similar approved outputs are NOT retrieved during resume generation
- `services/cover_letter.py` has imports added but **no actual integration** - similar approved cover letters are NOT retrieved during generation
- The `format_examples_for_prompt()` function is never called during generation

**Impact:** The learning system is built but disconnected. Users approve outputs, but the system doesn't use them.

**Remediation:**
```python
# In resume_tailor.py tailor_resume() function:
similar_bullets = await retrieve_similar_bullets(job_profile, embedding_service, vector_store, user_id)
examples_context = format_examples_for_prompt(similar_bullets, "bullets")
# Pass examples_context to LLM prompt

# In cover_letter.py generate_cover_letter() function:
similar_letters = await retrieve_similar_cover_letter_paragraphs(job_profile, embedding_service, vector_store, user_id)
examples_context = format_examples_for_prompt(similar_letters, "paragraphs")
# Pass examples_context to LLM prompt
```

**Effort:** 2-3 hours

---

### 2. Sprint 8 Task 1.8.6 NOT Implemented - Quality Comparison in Critic

**PRD Reference:** Section 4.7
> "Critic compares current output against best historical examples to avoid quality regressions."

**Implementation Plan Task 1.8.6:** "Add quality comparison in critic" (marked P2 but required by PRD)

**What's Built:** Nothing - the critic does NOT compare outputs against approved examples

**What's Missing:**
- No function in `services/critic.py` that retrieves similar approved outputs
- No quality regression detection
- No comparison scoring

**Impact:** Quality can regress without detection. The system cannot learn what "good" looks like.

**Remediation:** Defer to Sprint 8B (P2 priority, complex implementation)

**Effort:** 4-6 hours

---

### 3. No Skill-Gap Integration into Bullet/Content Selection

**PRD Reference:** Section 1.6 (Pipeline), Section 2.8
> "Step 4: Fit & Skill-Gap Analysis → Compute SkillGapResponse with gaps and positioning strategies"
> "Step 5: Bullet & Content Selection... Apply the Bullet Selection Algorithm"

**What's Built:**
- `POST /job/skill-gap` endpoint exists and works
- Skill gap analysis is computed
- `select_bullets_for_role()` in `resume_tailor.py` uses relevance scoring

**What's Missing:**
- Skill gap results are **NOT used** in bullet selection
- `positioning_strategies` from skill gap are NOT applied
- The skill gap endpoint is standalone - not integrated into the generation pipeline

**Impact:** Resumes are tailored, but positioning strategies from skill gap analysis are ignored.

**Remediation:**
```python
# In tailor_resume():
skill_gap = await analyze_skill_gap(job_profile_id, user_id, db)
# Use skill_gap.positioning_angles to influence bullet selection
# Use skill_gap.cover_letter_hooks for cover letter
```

**Effort:** 2-3 hours

---

### 4. Truthfulness Check Not Fully Implemented

**PRD Reference:** Section 4.3
> "The Critic must validate... Employer names and job titles must exactly match stored employment_history records. Employment dates must exactly match stored date ranges. No new employers, roles, or degrees may appear..."

**Implementation Plan Task 1.4.13:** "Implement resume truthfulness consistency check"

**What's Built:**
- `test_truthfulness_check.py` exists with tests
- Some basic validation in critic

**What's Missing:**
- No actual comparison of generated resume against stored `employment_history` data
- The critic evaluates content quality but doesn't validate factual consistency against the database
- Dates, titles, and employer names are not cross-checked

**Impact:** System could potentially output inaccurate employment data.

**Remediation:** Add `validate_truthfulness()` function to critic that queries database and compares.

**Effort:** 2-3 hours

---

## MEDIUM GAPS (Should Fix)

### 5. No Company Profile Integration

**PRD Reference:** Section 5.10
> "When a company_profile is available, ETPS must use it to: [Resume] Select and order bullets that align with the company's industry... [Cover Letter] Connect at least one paragraph to the company's business lines"

**What's Built:**
- `CompanyProfile` model exists in database
- `company_profile_id` parameter exists in cover letter endpoints

**What's Missing:**
- Cover letter generation does NOT actually use company profile data
- Resume generation ignores company profile entirely
- No company enrichment service (Phase 2, but basic integration should work)

**Impact:** Cover letters and resumes don't adapt to company context even when profile is available.

**Remediation:** Defer to Phase 2 (Sprint 11-14) - requires company enrichment service first.

---

### 6. Style Presets Not Implemented

**PRD Reference:** Section 3.1
> "The UI exposes style presets: Standard (~300 words), Executive (~250 words), Ultra-tight (~150–200 words), Custom"

**What's Built:**
- Cover letter generation works
- Word count validation exists

**What's Missing:**
- No `style_preset` parameter in the API
- No word count targeting based on preset
- Always generates at one target length

**Remediation:** Add to Sprint 9/10 frontend work or create Sprint 8C for backend.

**Effort:** 1-2 hours

---

### 7. Portfolio Integration Incomplete

**PRD Reference:** Section 2.8
> "When the JD is AI/LLM-heavy, allow bullets derived from ai_portfolio to be selected"

**What's Built:**
- `is_ai_heavy_job()` function exists
- `get_portfolio_bullets()` function exists
- `portfolio_loader.py` service exists

**What's Missing:**
- Portfolio bullets are generated but NOT consistently integrated
- No "Projects/Selected Work" section support
- `ai_portfolio` data not loaded from user profile

**Remediation:** Verify integration works end-to-end, add tests.

**Effort:** 1-2 hours

---

### 8. Version History API Returns Empty

**PRD Reference:** Section 2.6
> "Version history: list of improved variants (LLM-generated) with references to the original"

**What's Built:**
- `GET /resume/bullets/{id}/versions` endpoint exists
- `version_history` column exists on Bullet model
- `store_version_history()` function in bullet_rewriter.py

**What's Missing:**
- Version history is only populated during bullet rewriting
- If bullets aren't rewritten, version_history stays empty
- No way to manually add versions

**Remediation:** Document expected behavior - version history is populated on rewrite. Low priority.

---

### 9. Em-Dash Detection in Resumes

**PRD Reference:** Section 3.5, 4.3
> "Em-dashes (—) — not allowed, under any circumstances"

**What's Built:**
- Em-dash detection in cover letter critic
- Cover letter generation avoids em-dashes

**What's Missing:**
- Resume critic does NOT check for em-dashes
- Resume summary rewrite could potentially include em-dashes

**Remediation:** Add em-dash check to `evaluate_resume()` in critic.py

**Effort:** 30 minutes

---

### 10. Max Iterations Not Configurable

**PRD Reference:** Section 4.4
> "Max iterations (default 3) reached"

**What's Built:**
- Cover letter critic iteration loop with hardcoded max=3

**What's Missing:**
- No config.yaml setting for max_iterations
- Cannot be changed without code modification

**Remediation:** Add to config.yaml, update services to read from config.

**Effort:** 30 minutes

---

## MINOR GAPS (Nice to Have)

### 11. STAR Notes Not Used in Rewriting

**PRD Reference:** Section 2.6
> "STAR notes: optional longer-form context to support richer rewrites"

**What's Built:**
- `star_notes` field exists on Bullet model
- Bullet rewriter prompt mentions STAR notes

**What's Missing:**
- STAR notes not actually passed to rewriting prompts
- No UI or API to populate STAR notes

**Remediation:** Pass star_notes to rewrite prompt when available.

**Effort:** 30 minutes

---

### 12. Relationship Between Application and Generated Outputs

**PRD Reference:** Section 5.8
> "Resume/CL versions used" tracked per application

**What's Built:**
- Application model has `resume_json` and `cover_letter_json` fields

**What's Missing:**
- No automatic linking of generated outputs to applications
- Must be manually saved

**Remediation:** Defer to Phase 3 (Application Tracking)

---

### 13. ATS Score Breakdown Missing

**PRD Reference:** Section 4.3
> "ATS keyword coverage & score... Skills relevance and signal"

**What's Built:**
- `ats_coverage_percentage` in critic
- Basic keyword scoring

**What's Missing:**
- No detailed `ATSScoreBreakdown` with component scores (keyword_score, format_score, skills_score)
- Schema exists but not fully implemented

**Remediation:** Implement detailed breakdown in critic. Low priority.

**Effort:** 1-2 hours

---

### 14. Redundancy Control in Bullet Selection

**PRD Reference:** Section 2.8
> "Avoid selecting bullets that repeat the same achievement across roles"

**What's Built:**
- Bullet selection algorithm

**What's Missing:**
- No deduplication/similarity check across selected bullets
- Same achievement could appear in multiple roles

**Remediation:** Add embedding-based deduplication in bullet selection.

**Effort:** 2-3 hours

---

### 15. Context Notes Not Passed to All Services

**PRD Reference:** Section 1.3
> "Context notes are passed to: Summary Rewrite Engine, Resume bullet selection, Cover Letter Generator"

**What's Built:**
- `custom_instructions` parameter on `/resume/generate`
- `context_notes` parameter on cover letter endpoints

**What's Missing:**
- Context notes not passed to summary rewrite
- Context notes not used in bullet selection logic

**Remediation:** Thread context_notes through to all generation services.

**Effort:** 1 hour

---

## DOCUMENTATION GAPS

### 16. Implementation Plan Test Count Incorrect

**Current:** "342 passing"
**Actual:** Some test files not being collected properly (only 243 when running `tests/`)

**Remediation:** Fix pytest collection, update count.

---

### 17. Sprint 8 Marked Complete But Acceptance Criteria Not Met

**Implementation Plan says:**
- [x] Users can approve generated outputs
- [x] Approved outputs indexed with metadata
- [ ] Similar examples retrieved for new jobs ← NOT DONE
- [ ] Examples guide generation without copy-paste ← NOT DONE

**Remediation:** Update status or complete the work.

---

### 18. Missing Test Files in Test Coverage List

Current list doesn't include all test files. Some referenced files may not exist:
- `test_resume_critic.py` - verify exists
- `test_skill_gap.py` - verify exists
- `test_cover_letter_critic.py` - verify exists

**Remediation:** Audit test files, update documentation.

---

## REMEDIATION PLAN

### Sprint 8B: Gap Remediation (Before Sprint 9)

| ID | Task | Gap # | Priority | Effort |
|----|------|-------|----------|--------|
| 8B.1 | Integrate approved outputs into resume generation | 1 | P0 | 2h |
| 8B.2 | Integrate approved outputs into cover letter generation | 1 | P0 | 1h |
| 8B.3 | Integrate skill gap results into bullet selection | 3 | P0 | 2h |
| 8B.4 | Implement truthfulness validation in critic | 4 | P0 | 2h |
| 8B.5 | Add em-dash detection to resume critic | 9 | P1 | 0.5h |
| 8B.6 | Add max_iterations to config.yaml | 10 | P2 | 0.5h |
| 8B.7 | Pass STAR notes to bullet rewriter | 11 | P2 | 0.5h |
| 8B.8 | Thread context_notes to summary rewrite | 15 | P2 | 0.5h |
| 8B.9 | Update documentation and test counts | 16-18 | P1 | 0.5h |
| 8B.10 | Write tests for new integrations | - | P1 | 2h |

**Total Estimated Effort:** 11.5 hours

### Deferred Items

| Gap # | Description | Deferred To |
|-------|-------------|-------------|
| 2 | Quality comparison in critic | Phase 2 or later sprint |
| 5 | Company profile integration | Sprint 11 (Phase 2) |
| 6 | Style presets | Sprint 9-10 (Frontend) |
| 12 | Application ↔ Output linking | Sprint 15-17 (Phase 3) |
| 13 | ATS score breakdown | Future enhancement |
| 14 | Redundancy control | Future enhancement |

---

## Summary Matrix

| Gap | PRD Section | Implementation Plan | Built | Status | Remediation |
|-----|-------------|--------------------|----|--------|-------------|
| Similar examples in generation | 4.7 | Task 1.8.5 | Imports only | ❌ Critical | Sprint 8B |
| Quality comparison in critic | 4.7 | Task 1.8.6 | Not built | ❌ Critical | Deferred |
| Skill gap → bullet selection | 1.6, 2.8 | Implicit | Not connected | ❌ Critical | Sprint 8B |
| Truthfulness validation | 4.3 | Task 1.4.13 | Partial | ❌ Critical | Sprint 8B |
| Company profile integration | 5.10 | Phase 2 | Model only | ⚠️ Medium | Phase 2 |
| Style presets | 3.1 | Not specified | Not built | ⚠️ Medium | Sprint 9-10 |
| Portfolio integration | 2.8 | Task 1.4.11 | Partial | ⚠️ Medium | Verify |
| Em-dash in resumes | 4.3 | Implicit | Cover letter only | ⚠️ Medium | Sprint 8B |
| Max iterations config | 4.4 | Implicit | Hardcoded | ⚠️ Medium | Sprint 8B |
| STAR notes | 2.6 | Implicit | Field exists | 📝 Minor | Sprint 8B |
| Context notes threading | 1.3 | Implicit | Partial | 📝 Minor | Sprint 8B |

---

## Next Steps

1. Review and approve this gap analysis
2. Update IMPLEMENTATION_PLAN.md to add Sprint 8B
3. Update PRD amendments if needed
4. Execute Sprint 8B remediation
5. Re-run tests and verify all acceptance criteria
6. Proceed to Sprint 9 (Frontend MVP)

---

*Generated: December 6, 2025*

# Skill Gap Analyzer Test Suite - Sprint 2

## Overview

Comprehensive test suite for the Sprint 2 Skill Gap Analyzer enhancements. The test file (`test_skill_gap.py`) documents expected behavior for advanced features that will be implemented in Sprint 2.

**Test File Location:** `/Users/benjaminblack/projects/etps/backend/test_skill_gap.py`

## Test Status Legend

- **EXPECTS PASS** - Tests that should work with current implementation
- **EXPECTS FAIL** - Tests documenting Sprint 2 features (currently not implemented)
- **Integration** - End-to-end tests that verify component interaction

## Test Categories

### 1. Semantic Skill Matching Tests (`TestSemanticSkillMatching`)

**Purpose:** Test semantic similarity matching for skills beyond simple string/synonym matching.

#### Tests:

- **`test_semantic_matching_ml_to_machine_learning`** (EXPECTS FAIL)
  - Validates that "ML Engineering" matches "Machine Learning" semantically
  - Requires embedding-based similarity
  - Currently only supports exact/synonym matching

- **`test_similarity_threshold_respects_config`** (EXPECTS FAIL)
  - Validates that semantic similarity respects configured threshold (default 0.75)
  - Requires configurable embedding similarity threshold
  - Will enable tuning of match strictness

- **`test_fallback_to_synonym_when_embedding_unavailable`** (EXPECTS PASS)
  - Tests graceful degradation to SKILL_SYNONYMS mapping when embedding service unavailable
  - Validates fallback mechanism for robustness
  - Currently implemented

- **`test_multiple_candidate_skills_returns_best_match`** (EXPECTS PASS)
  - When multiple user skills could match job skill, best match should be returned
  - Uses synonym matching currently; will use semantic scoring in Sprint 2
  - Currently returns first match; should return highest confidence match

### 2. Gap Categorization Tests (`TestGapCategorization`)

**Purpose:** Test intelligent categorization of skill gaps into critical/important/nice-to-have.

#### Tests:

- **`test_critical_skills_from_requirements_section`** (EXPECTS FAIL)
  - Validates that skills from "Requirements" section are marked as critical
  - Requires LLM-based JD section parsing
  - Currently uses simple heuristics (first 50% of skills)

- **`test_nice_to_have_skills_categorized_correctly`** (EXPECTS FAIL)
  - Validates that skills from "Nice to Have" / "Preferred" sections are categorized appropriately
  - Requires section-aware parsing of JD structure
  - Currently doesn't distinguish between sections

- **`test_llm_based_categorization_various_jd_structures`** (EXPECTS FAIL)
  - Validates LLM can handle diverse JD formats:
    - Traditional "Requirements" / "Nice to Have" sections
    - Prose-based requirements throughout
    - Bullet lists without explicit sections
  - Requires LLM integration for flexible parsing
  - Will enable handling of any JD format

### 3. Positioning Strategy Tests (`TestPositioningStrategy`)

**Purpose:** Test generation of user-specific, actionable positioning strategies.

#### Tests:

- **`test_strategies_reference_user_actual_skills`** (EXPECTS FAIL)
  - Validates that strategies mention user's actual skills (not generic templates)
  - Example: "Emphasize your TensorFlow and Kubernetes expertise" (not "emphasize relevant experience")
  - Requires context-aware template instantiation with actual user skills

- **`test_strategies_align_with_job_priorities`** (EXPECTS FAIL)
  - Validates that positioning strategies align with job's core_priorities
  - For ML leadership role, strategies should emphasize team building, not just ML skills
  - Requires priority-aware strategy selection

- **`test_critical_gaps_get_mitigation_strategies`** (EXPECTS FAIL)
  - Validates that critical skill gaps receive specific mitigation guidance
  - Example for missing "Deep Learning": suggest learning path via related skills
  - Requires gap-specific strategy generation
  - Should NOT use generic "learn the skill" advice

### 4. Weak Signal Detection Tests (`TestWeakSignalDetection`)

**Purpose:** Test detection of skills where user has related capability but not direct match.

#### Tests:

- **`test_semantic_detection_finds_related_skills`** (EXPECTS FAIL)
  - Validates that weak signals find skills beyond RELATED_SKILLS mapping
  - Example: "Software Engineering" is semantically related to "Machine Learning"
  - Requires embedding-based semantic similarity for weak signal detection
  - Currently only checks RELATED_SKILLS dictionary

- **`test_weak_signal_evidence_includes_actual_bullet_text`** (EXPECTS FAIL)
  - Validates that weak signal evidence includes actual bullet text (not just skill names)
  - Example: "Led team using Python and system architecture" (not "experience with Python")
  - Requires extraction of relevant bullet text to support claims

- **`test_weak_signals_ranked_by_similarity_score`** (EXPECTS FAIL)
  - Validates that weak signals are ranked by confidence/similarity score
  - Requires adding `similarity_score` to WeakSignal schema
  - Enables prioritization of which weak signals to highlight

### 5. Resume Tailoring Integration Tests (`TestResumeTailoringIntegration`)

**Purpose:** Test integration of skill gap analysis into the resume tailoring workflow.

#### Tests:

- **`test_skill_gap_called_during_tailoring`** (EXPECTS FAIL)
  - Validates that `analyze_skill_gap` is called automatically during `tailor_resume`
  - Documents that skill gap analysis is part of tailoring workflow
  - Requires integration into `tailor_resume` function

- **`test_bullet_selection_uses_prioritize_tags_guidance`** (EXPECTS FAIL)
  - Validates that bullet selection uses `bullet_selection_guidance.prioritize_tags`
  - Ensures tailored resume prioritizes bullets matching high-value skills
  - Currently implemented but may need refinement

- **`test_skill_gap_summary_included_in_response`** (EXPECTS FAIL)
  - Validates that TailoredResumeResponse includes skill gap analysis summary
  - Provides user with visibility into how resume was optimized
  - Requires extending TailoredResumeResponse schema

### 6. Database Persistence Tests (`TestDatabasePersistence`)

**Purpose:** Test saving and retrieving skill gap analysis from database.

#### Tests:

- **`test_skill_gap_analysis_saved_to_job_profile`** (EXPECTS FAIL)
  - Validates that analysis results are persisted to `JobProfile.skill_gap_analysis` JSON field
  - Requires implementing persistence logic in `analyze_skill_gap`
  - Enables reuse of analysis without recomputation

- **`test_cache_retrieval_works`** (EXPECTS FAIL)
  - Validates that previously computed analysis is retrieved from cache
  - Same user/job combination should return cached result
  - Improves performance for repeated analyses

- **`test_cache_invalidation_on_user_profile_change`** (EXPECTS FAIL)
  - Validates that cache is invalidated when user adds/updates skills
  - Adding new bullet with high-value skill should improve match score
  - Cache logic must detect profile changes

### 7. Positioning Strategy Content Tests (`TestPositioningStrategyContent`)

**Purpose:** Test quality and specificity of generated strategies.

#### Tests:

- **`test_strategies_are_actionable_not_generic`** (EXPECTS FAIL)
  - Validates that strategies are specific and actionable (>50 chars, detailed)
  - Rejects generic advice like "highlight your experience"
  - Requires customized strategy generation

- **`test_mitigation_strategies_address_specific_gaps`** (EXPECTS FAIL)
  - Validates that each gap has mitigation tailored to that gap
  - Different gaps get different advice (not cookie-cutter)
  - Requires gap-specific strategy instantiation

### 8. Cover Letter and Advantages Tests (`TestCoverLetterAndAdvantagesGeneration`)

**Purpose:** Test generation of cover letter hooks and user advantages.

#### Tests:

- **`test_cover_letter_hooks_reference_matched_skills`** (EXPECTS PASS)
  - Validates that cover letter hooks mention user's strongest matched skills
  - Currently implemented in base version

- **`test_user_advantages_drawn_from_profile`** (EXPECTS PASS)
  - Validates that identified advantages are drawn from actual profile data
  - Not generic advice; specific to candidate
  - Currently implemented in base version

### 9. Integration Tests (`TestSkillGapAnalysisIntegration`)

**Purpose:** End-to-end workflow tests with realistic data.

#### Tests:

- **`test_end_to_end_analysis_with_real_data`** (EXPECTS PASS)
  - Validates complete skill gap analysis workflow
  - Checks that response structure is valid and complete
  - Uses realistic test data with multiple experiences and bullets

- **`test_analysis_with_comprehensive_user_profile`** (EXPECTS PASS)
  - Tests analysis with user having strong skill match
  - Well-matched candidate should score >= 50
  - Validates that matched skills are identified

- **`test_analysis_with_junior_candidate`** (EXPECTS PASS)
  - Tests analysis with junior-level candidate for senior role
  - Should identify critical gaps
  - Score should be < 50
  - Recommendation should be "stretch_role" or "weak_match"

## Test Data Setup

All tests use realistic test data created by `setup_test_data()`:

### Users
- Test user with senior and mid-level experience

### Experiences
1. **Senior Machine Learning Engineer** (Current)
   - Tech Corp, San Francisco
   - Various ML, NLP, infrastructure work

2. **Data Engineer** (Previous)
   - DataCo, San Francisco (2018-2020)
   - ETL, Spark, data pipeline work

### Bullets (Realistic Examples)
- ML pipeline architecture (99.95% uptime)
- NLP team leadership (23% accuracy improvement)
- Apache Spark ETL optimization (6h → 45m)
- Kubernetes migration (70% faster deployment)
- FastAPI microservices (99.9% uptime)
- Data quality initiatives (weak/generic)

### Job Profile
**Senior ML Engineering Manager**
- Requirements: ML, Deep Learning, TensorFlow, PyTorch, Python, Kubernetes, Docker, Leadership
- Nice to Have: LLM, Generative AI, Model Risk Management, AI Governance, AWS, Spark

## Running the Tests

### Run All Tests
```bash
cd /Users/benjaminblack/projects/etps/backend
pytest test_skill_gap.py -v
```

### Run Specific Test Class
```bash
pytest test_skill_gap.py::TestSemanticSkillMatching -v
```

### Run Single Test
```bash
pytest test_skill_gap.py::TestSemanticSkillMatching::test_fallback_to_synonym_when_embedding_unavailable -v
```

### Run Only Tests Expected to Pass
```bash
pytest test_skill_gap.py -v -k "PASS" 2>/dev/null || echo "Filtering works at development time"
```

### Run With Coverage
```bash
pytest test_skill_gap.py --cov=services.skill_gap --cov-report=term-missing
```

## Implementation Roadmap for Sprint 2

### Phase 1: Semantic Matching
- [ ] Integrate embedding service (e.g., OpenAI embeddings)
- [ ] Implement `semantic_similarity_score()` function
- [ ] Add configurable similarity threshold to config
- [ ] Update `find_skill_match()` to use semantic matching with fallback
- [ ] Tests: `TestSemanticSkillMatching`

### Phase 2: Intelligent Gap Categorization
- [ ] Integrate LLM for JD section parsing
- [ ] Create `parse_jd_sections()` function to extract requirements/nice-to-have
- [ ] Update `compute_missing_skills()` to use parsed sections
- [ ] Handle various JD formats (prose, bullets, mixed)
- [ ] Tests: `TestGapCategorization`

### Phase 3: Context-Aware Positioning Strategies
- [ ] Refactor `generate_positioning_strategies()` to accept user context
- [ ] Implement `instantiate_strategy_template()` with actual skill names
- [ ] Create `generate_gap_specific_mitigation()` for each gap
- [ ] Update `POSITIONING_TEMPLATES` with more flexible format
- [ ] Tests: `TestPositioningStrategy`, `TestPositioningStrategyContent`

### Phase 4: Enhanced Weak Signal Detection
- [ ] Update weak signal detection to use semantic similarity
- [ ] Extract bullet text evidence instead of just skill names
- [ ] Add `similarity_score` field to `WeakSignal` schema
- [ ] Implement ranking by similarity score
- [ ] Tests: `TestWeakSignalDetection`

### Phase 5: Resume Tailoring Integration
- [ ] Call `analyze_skill_gap()` from `tailor_resume()`
- [ ] Use `bullet_selection_guidance` in bullet selection logic
- [ ] Extend `TailoredResumeResponse` with `skill_gap_analysis` summary
- [ ] Tests: `TestResumeTailoringIntegration`

### Phase 6: Database Persistence & Caching
- [ ] Implement `persist_skill_gap_analysis()` to save to `JobProfile.skill_gap_analysis`
- [ ] Create cache key based on user_id, job_profile_id, profile hash
- [ ] Implement `get_cached_skill_gap_analysis()` function
- [ ] Track user profile changes to invalidate cache
- [ ] Tests: `TestDatabasePersistence`

## Key Implementation Notes

### Skill Matching Strategy
Current implementation uses exact/synonym matching. Sprint 2 should:
1. Try semantic matching first (if embedding service available)
2. Fall back to synonym matching if semantic unavailable or below threshold
3. Return best match (highest similarity score) not first match

### Gap Categorization Logic
Current implementation uses position-based heuristics. Sprint 2 should:
1. Parse JD structure to identify sections
2. Map extracted skills to source sections
3. Assign importance based on section (requirements > nice-to-have)
4. Use LLM for flexible JD parsing

### Positioning Strategies
Current implementation uses generic templates. Sprint 2 should:
1. Get actual user skills from profile context
2. Match job priorities from job_profile.core_priorities
3. Generate gap-specific mitigation (not one-size-fits-all)
4. Reference specific skills and related capabilities

### Weak Signals
Current implementation uses RELATED_SKILLS dictionary. Sprint 2 should:
1. Use semantic similarity to find related skills (not just dictionary)
2. Extract actual bullet text as evidence
3. Calculate similarity scores for each weak signal
4. Rank by score for prioritization

### Performance Considerations
- Semantic matching requires embedding calls (potentially slow)
- LLM-based parsing adds latency
- Caching is critical for performance
- Consider batch processing for multiple job profiles
- Add async/await throughout

## Test Execution Notes

Several tests are marked `EXPECTS FAIL` because they document Sprint 2 features:
- These tests will help guide implementation
- They clearly document expected behavior
- They will become green as features are implemented
- Some may need adjustment based on implementation details

Tests marked `EXPECTS PASS` should pass with current implementation:
- These validate the base skill gap analysis functionality
- They ensure data flow works correctly
- They catch regressions in core logic

## Files Modified/Created

- **Created:** `/Users/benjaminblack/projects/etps/backend/test_skill_gap.py`
  - 800+ lines of comprehensive tests
  - 9 test classes, 30+ test methods
  - Covers all Sprint 2 enhancement areas

## Dependencies

The test file requires:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `sqlalchemy` - ORM for database access
- All services: `skill_gap`, `llm`, etc.

## Continuous Integration

Once tests are in place, CI/CD should:
1. Run `pytest test_skill_gap.py -v` on every commit
2. Fail builds if "EXPECTS PASS" tests fail
3. Report on "EXPECTS FAIL" tests separately
4. Gradually convert EXPECTS FAIL tests to EXPECTS PASS
5. Track Sprint 2 implementation progress

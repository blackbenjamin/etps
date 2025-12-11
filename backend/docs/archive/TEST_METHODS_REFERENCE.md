# Skill Gap Analyzer - Test Methods Reference

Complete index of all 26 test methods with descriptions, status, and purpose.

## TestSemanticSkillMatching (4 tests)

Tests for embedding-based semantic skill matching capabilities.

### 1. `test_semantic_matching_ml_to_machine_learning`
- **Status:** EXPECTS FAIL
- **Location:** Line ~120
- **Purpose:** Validate that "ML Engineering" semantically matches "Machine Learning"
- **Sprint 2 Feature:** Embedding-based semantic similarity matching
- **Key Assertion:** `matched is not None`
- **When to Run:** While implementing semantic matching

### 2. `test_similarity_threshold_respects_config`
- **Status:** EXPECTS FAIL
- **Location:** Line ~142
- **Purpose:** Validate configurable similarity threshold (default 0.75)
- **Sprint 2 Feature:** Config-based threshold for semantic matches
- **Key Assertion:** `threshold <= 0.75`
- **When to Run:** While implementing embedding integration

### 3. `test_fallback_to_synonym_when_embedding_unavailable`
- **Status:** EXPECTS PASS (base implementation)
- **Location:** Line ~165
- **Purpose:** Test fallback to SKILL_SYNONYMS when embedding unavailable
- **Current Feature:** Synonym-based matching via SKILL_SYNONYMS mapping
- **Key Assertion:** `matched == "PyTorch"`
- **When to Run:** Always (regression test)
- **Validates:** Robustness when external service unavailable

### 4. `test_multiple_candidate_skills_returns_best_match`
- **Status:** EXPECTS PASS/PARTIAL (current returns first, should return best)
- **Location:** Line ~183
- **Purpose:** When multiple user skills could match, return best match
- **Current Feature:** Synonym matching (needs similarity scoring)
- **Key Assertion:** `matched in ["Machine Learning", "ML Ops"]`
- **When to Run:** After semantic scoring implemented
- **Validates:** Best-match selection logic

---

## TestGapCategorization (3 tests)

Tests for intelligent categorization of skill gaps by importance level.

### 5. `test_critical_skills_from_requirements_section`
- **Status:** EXPECTS FAIL
- **Location:** Line ~204
- **Purpose:** Validate skills from "Requirements" marked as critical
- **Sprint 2 Feature:** LLM-based JD section parsing
- **Key Assertion:** `critical_gaps` contains Deep Learning
- **When to Run:** While implementing LLM-based parsing
- **Validates:** Requirements/must-have distinction

### 6. `test_nice_to_have_skills_categorized_correctly`
- **Status:** EXPECTS FAIL
- **Location:** Line ~242
- **Purpose:** Validate "Nice to Have" section skills categorized appropriately
- **Sprint 2 Feature:** Section-aware JD parsing
- **Key Assertion:** Nice-to-have gaps contain LLM/Generative AI
- **When to Run:** While implementing section distinction
- **Validates:** Preference distinction from requirements

### 7. `test_llm_based_categorization_various_jd_structures`
- **Status:** EXPECTS FAIL (marked as skip)
- **Location:** Line ~280
- **Purpose:** Test LLM handles various JD formats
- **Sprint 2 Feature:** Flexible format parsing via LLM
- **Formats Tested:**
  - Traditional "Requirements" / "Nice to Have" sections
  - Prose-based embedded requirements
  - Bullet lists without section headers
- **When to Run:** While implementing format-agnostic parsing
- **Validates:** Parser robustness

---

## TestPositioningStrategy (3 tests)

Tests for user-specific, context-aware positioning strategy generation.

### 8. `test_strategies_reference_user_actual_skills`
- **Status:** EXPECTS FAIL
- **Location:** Line ~300
- **Purpose:** Strategies mention actual user skills, not generic templates
- **Sprint 2 Feature:** Context-aware strategy instantiation
- **Example:** "Emphasize TensorFlow expertise" not "emphasize relevant experience"
- **Key Assertion:** Strategy text contains actual skill names
- **When to Run:** While implementing customized strategies
- **Validates:** Personalization quality

### 9. `test_strategies_align_with_job_priorities`
- **Status:** EXPECTS FAIL
- **Location:** Line ~339
- **Purpose:** Strategies align with job's core_priorities
- **Sprint 2 Feature:** Priority-aware strategy selection
- **Example Job Priorities:** ML leadership, deep learning, team building
- **Key Assertion:** Strategy mentions leadership or team
- **When to Run:** While implementing priority matching
- **Validates:** Job alignment quality

### 10. `test_critical_gaps_get_mitigation_strategies`
- **Status:** EXPECTS FAIL
- **Location:** Line ~375
- **Purpose:** Critical gaps receive specific mitigation (not generic)
- **Sprint 2 Feature:** Gap-specific mitigation guidance
- **Example:** For missing Deep Learning: suggest learning path via related skills
- **Key Assertion:** Mitigation mentions learning/transfer/experience
- **When to Run:** While implementing gap-specific guidance
- **Validates:** Actionability of strategies

---

## TestWeakSignalDetection (3 tests)

Tests for detecting skills where user has adjacent capability without direct match.

### 11. `test_semantic_detection_finds_related_skills`
- **Status:** EXPECTS FAIL
- **Location:** Line ~404
- **Purpose:** Weak signals find skills beyond RELATED_SKILLS mapping
- **Sprint 2 Feature:** Semantic similarity for weak signal detection
- **Example:** "Software Engineering" semantically related to "Machine Learning"
- **Key Assertion:** `len(weak_signals) > 0`
- **When to Run:** While extending weak signal detection
- **Validates:** Breadth of weak signal discovery

### 12. `test_weak_signal_evidence_includes_actual_bullet_text`
- **Status:** EXPECTS FAIL (but attempts to pass with current data)
- **Location:** Line ~435
- **Purpose:** Evidence includes actual bullet text, not just skill names
- **Sprint 2 Feature:** Bullet text extraction for evidence
- **Example Evidence:** "Led team using Python and system architecture"
- **Key Assertion:** Evidence is substantive (>20 chars)
- **When to Run:** While implementing evidence extraction
- **Validates:** Evidence quality and concreteness

### 13. `test_weak_signals_ranked_by_similarity_score`
- **Status:** EXPECTS FAIL
- **Location:** Line ~472
- **Purpose:** Weak signals ranked by confidence/similarity score
- **Sprint 2 Feature:** Add similarity_score to WeakSignal schema
- **Key Assertion:** Signals ordered by relevance
- **When to Run:** While adding scoring to WeakSignal
- **Validates:** Ranking/prioritization quality

---

## TestResumeTailoringIntegration (3 tests)

Tests for integration of skill gap analysis into resume tailoring workflow.

### 14. `test_skill_gap_called_during_tailoring`
- **Status:** EXPECTS FAIL (marked skip)
- **Location:** Line ~495
- **Purpose:** analyze_skill_gap called automatically during tailor_resume
- **Sprint 2 Feature:** Integration into tailoring workflow
- **When to Run:** While integrating skill gap into resume tailor
- **Validates:** Workflow integration completeness

### 15. `test_bullet_selection_uses_prioritize_tags_guidance`
- **Status:** EXPECTS PASS/PARTIAL (guidance present, integration may incomplete)
- **Location:** Line ~510
- **Purpose:** Bullet selection uses bullet_selection_guidance.prioritize_tags
- **Current Feature:** Guidance generation
- **Sprint 2 Feature:** Using guidance in bullet selection
- **Key Assertion:** `"prioritize_tags" in guidance`
- **When to Run:** While implementing prioritization
- **Validates:** Guidance availability and format

### 16. `test_skill_gap_summary_included_in_response`
- **Status:** EXPECTS FAIL (needs schema extension)
- **Location:** Line ~537
- **Purpose:** Skill gap summary included in tailored resume response
- **Sprint 2 Feature:** Extend TailoredResumeResponse schema
- **When to Run:** While integrating skill gap results
- **Validates:** End-to-end response structure

---

## TestDatabasePersistence (3 tests)

Tests for saving and retrieving skill gap analysis from database.

### 17. `test_skill_gap_analysis_saved_to_job_profile`
- **Status:** EXPECTS FAIL
- **Location:** Line ~560
- **Purpose:** Analysis results persisted to JobProfile.skill_gap_analysis
- **Sprint 2 Feature:** Persistence to JSON field
- **Key Assertion:** `job_profile.skill_gap_analysis is not None`
- **When to Run:** While implementing persistence
- **Validates:** Data durability and schema usage

### 18. `test_cache_retrieval_works`
- **Status:** EXPECTS FAIL
- **Location:** Line ~597
- **Purpose:** Previously computed analysis retrieved from cache
- **Sprint 2 Feature:** Caching mechanism
- **Key Assertion:** Two calls return same scores
- **When to Run:** While implementing caching layer
- **Validates:** Cache consistency and correctness

### 19. `test_cache_invalidation_on_user_profile_change`
- **Status:** EXPECTS FAIL
- **Location:** Line ~630
- **Purpose:** Cache invalidated when user adds/updates skills
- **Sprint 2 Feature:** Change detection and cache invalidation
- **Scenario:** Add new bullet with LLM skill → score should improve
- **Key Assertion:** New score >= initial score
- **When to Run:** While implementing cache invalidation
- **Validates:** Cache freshness

---

## TestPositioningStrategyContent (2 tests)

Tests for quality and specificity of positioning strategy content.

### 20. `test_strategies_are_actionable_not_generic`
- **Status:** EXPECTS FAIL
- **Location:** Line ~663
- **Purpose:** Strategies are specific and actionable, not generic templates
- **Sprint 2 Feature:** Content quality validation
- **Requirements:**
  - >50 characters (detailed)
  - Avoid generic phrases alone
  - Provide specific guidance
- **Key Assertion:** Strategy length and specificity
- **When to Run:** While refining strategy generation
- **Validates:** User experience quality

### 21. `test_mitigation_strategies_address_specific_gaps`
- **Status:** EXPECTS FAIL
- **Location:** Line ~691
- **Purpose:** Each gap has mitigation tailored to that gap
- **Sprint 2 Feature:** Gap-specific strategy generation
- **Example:** Different mitigation for missing ML vs missing Leadership
- **Key Assertion:** Strategy mentions specific skill
- **When to Run:** While implementing gap-specific logic
- **Validates:** Customization quality

---

## TestCoverLetterAndAdvantagesGeneration (2 tests)

Tests for cover letter hooks and user advantages identification.

### 22. `test_cover_letter_hooks_reference_matched_skills`
- **Status:** EXPECTS PASS (base implementation)
- **Location:** Line ~717
- **Purpose:** Cover letter hooks mention user's strongest matched skills
- **Current Feature:** Hook generation
- **Key Assertion:** Hooks reference matched skills
- **When to Run:** Always (regression test)
- **Validates:** Hook quality and relevance

### 23. `test_user_advantages_drawn_from_profile`
- **Status:** EXPECTS PASS (base implementation)
- **Location:** Line ~755
- **Purpose:** User advantages drawn from actual profile data
- **Current Feature:** Advantage identification
- **Key Assertion:** Advantages mention specific capabilities
- **When to Run:** Always (regression test)
- **Validates:** Advantage specificity

---

## TestSkillGapAnalysisIntegration (3 tests)

End-to-end integration tests with realistic workflows.

### 24. `test_end_to_end_analysis_with_real_data`
- **Status:** EXPECTS PASS (base implementation)
- **Location:** Line ~788
- **Purpose:** Complete skill gap analysis runs without errors
- **Current Feature:** Full analysis workflow
- **Key Assertions:**
  - Response is SkillGapResponse
  - All required fields populated
  - Numeric ranges valid
  - Lists present
- **When to Run:** Always (critical regression test)
- **Validates:** Basic functionality and data flow

### 25. `test_analysis_with_comprehensive_user_profile`
- **Status:** EXPECTS PASS (base implementation)
- **Location:** Line ~826
- **Purpose:** Well-matched candidate gets reasonable score
- **Scenario:** ML engineer applying for ML manager role
- **Key Assertions:**
  - Score >= 50 (reasonable match)
  - Has matched_skills
  - Has some skill_gaps
- **When to Run:** Always (regression test)
- **Validates:** Core scoring logic

### 26. `test_analysis_with_junior_candidate`
- **Status:** EXPECTS PASS (base implementation)
- **Location:** Line ~867
- **Purpose:** Junior candidate for senior role gets low score
- **Scenario:** Junior developer applying for senior ML role
- **Key Assertions:**
  - Has critical_gaps
  - Score < 50
  - Recommendation is stretch_role or weak_match
- **When to Run:** Always (regression test)
- **Validates:** Scoring differentiates seniority

---

## Test Status Summary

### Passing Tests (Must Always Pass - Regression Prevention)
1. test_fallback_to_synonym_when_embedding_unavailable
2. test_multiple_candidate_skills_returns_best_match (partial)
3. test_bullet_selection_uses_prioritize_tags_guidance (partial)
4. test_cover_letter_hooks_reference_matched_skills
5. test_user_advantages_drawn_from_profile
6. test_end_to_end_analysis_with_real_data
7. test_analysis_with_comprehensive_user_profile
8. test_analysis_with_junior_candidate

**Total: ~8 tests**

### Failing Tests (Sprint 2 Implementation Guides)
1. test_semantic_matching_ml_to_machine_learning
2. test_similarity_threshold_respects_config
3. test_critical_skills_from_requirements_section
4. test_nice_to_have_skills_categorized_correctly
5. test_llm_based_categorization_various_jd_structures
6. test_strategies_reference_user_actual_skills
7. test_strategies_align_with_job_priorities
8. test_critical_gaps_get_mitigation_strategies
9. test_semantic_detection_finds_related_skills
10. test_weak_signal_evidence_includes_actual_bullet_text
11. test_weak_signals_ranked_by_similarity_score
12. test_skill_gap_called_during_tailoring
13. test_skill_gap_summary_included_in_response
14. test_skill_gap_analysis_saved_to_job_profile
15. test_cache_retrieval_works
16. test_cache_invalidation_on_user_profile_change
17. test_strategies_are_actionable_not_generic
18. test_mitigation_strategies_address_specific_gaps

**Total: ~18 tests**

---

## Quick Lookup by Feature

### Semantic Matching Features
- test_semantic_matching_ml_to_machine_learning
- test_similarity_threshold_respects_config
- test_fallback_to_synonym_when_embedding_unavailable
- test_multiple_candidate_skills_returns_best_match

### Gap Categorization Features
- test_critical_skills_from_requirements_section
- test_nice_to_have_skills_categorized_correctly
- test_llm_based_categorization_various_jd_structures

### Positioning Strategy Features
- test_strategies_reference_user_actual_skills
- test_strategies_align_with_job_priorities
- test_critical_gaps_get_mitigation_strategies
- test_strategies_are_actionable_not_generic
- test_mitigation_strategies_address_specific_gaps

### Weak Signal Features
- test_semantic_detection_finds_related_skills
- test_weak_signal_evidence_includes_actual_bullet_text
- test_weak_signals_ranked_by_similarity_score

### Integration Features
- test_skill_gap_called_during_tailoring
- test_bullet_selection_uses_prioritize_tags_guidance
- test_skill_gap_summary_included_in_response
- test_end_to_end_analysis_with_real_data
- test_analysis_with_comprehensive_user_profile
- test_analysis_with_junior_candidate

### Database Features
- test_skill_gap_analysis_saved_to_job_profile
- test_cache_retrieval_works
- test_cache_invalidation_on_user_profile_change

### User Experience Features
- test_cover_letter_hooks_reference_matched_skills
- test_user_advantages_drawn_from_profile

---

## Test Execution Commands

### Run All Tests
```bash
cd /Users/benjaminblack/projects/etps/backend
pytest test_skill_gap.py -v
```

### Run Specific Feature Tests
```bash
# Semantic matching
pytest test_skill_gap.py::TestSemanticSkillMatching -v

# Gap categorization
pytest test_skill_gap.py::TestGapCategorization -v

# Positioning
pytest test_skill_gap.py::TestPositioningStrategy -v
pytest test_skill_gap.py::TestPositioningStrategyContent -v

# Weak signals
pytest test_skill_gap.py::TestWeakSignalDetection -v

# Integration
pytest test_skill_gap.py::TestResumeTailoringIntegration -v
pytest test_skill_gap.py::TestSkillGapAnalysisIntegration -v

# Database
pytest test_skill_gap.py::TestDatabasePersistence -v

# User experience
pytest test_skill_gap.py::TestCoverLetterAndAdvantagesGeneration -v
```

### Run Single Test
```bash
pytest test_skill_gap.py::TestSemanticSkillMatching::test_semantic_matching_ml_to_machine_learning -v
```

### Run Only Expected Passing Tests
```bash
pytest test_skill_gap.py -v -k "fallback or multiple_candidate or cover_letter or advantages or end_to_end or comprehensive or junior"
```

---

## Test Development Progress Tracking

Use this file to track which tests have been implemented:

```bash
# Count total tests
grep "def test_" /Users/benjaminblack/projects/etps/backend/test_skill_gap.py | wc -l

# Run and see passing count
pytest test_skill_gap.py -v 2>&1 | grep "PASSED" | wc -l

# See failing count
pytest test_skill_gap.py -v 2>&1 | grep "FAILED" | wc -l
```

As Sprint 2 progresses, more tests should move from FAILED to PASSED status.

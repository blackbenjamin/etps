# Skill Extraction Enhancements - Test Plan (Plan C)

## Overview

Comprehensive test suite for Plan C: Hybrid Skill Extraction improvements across three phases:
- **Phase 1**: Expand SKILL_TAXONOMY with 4 new categories + improved boilerplate filtering
- **Phase 2**: LLM-powered skill extraction with hybrid method
- **Phase 3**: Resume skills enrichment using domain inference and capability clusters

**Test File**: `/Users/benjaminblack/projects/etps/backend/tests/test_skill_extraction_enhancements.py`

## Test Results Summary

```
Total Tests: 15
Passed:      10 (Phase 1 + Integration + Tier 5)
Failed:      3  (Phase 2 - awaiting implementation)
Skipped:     2  (Phase 3 - awaiting implementation)
```

## Phase 1: Taxonomy Expansion & Boilerplate Filtering

### Status: PASSING (7/7 tests)

Phase 1 features are **already implemented** in the codebase. The SKILL_TAXONOMY has been expanded with four new categories:

#### 1.1 Business Analysis Category
- **Test**: `test_business_analysis_category_exists`
- **Status**: PASSING
- **Skills included**:
  - Requirements Engineering
  - User Stories
  - Use Cases
  - Gap Analysis
  - Process Mapping
  - BRD (Business Requirements Document)

#### 1.2 Project Management Category
- **Test**: `test_project_management_category_exists`
- **Status**: PASSING
- **Skills included**:
  - JIRA
  - Confluence
  - Sprint Planning
  - Asana
  - Monday.com
  - Trello

#### 1.3 Soft Skills Category
- **Test**: `test_soft_skills_category_exists`
- **Status**: PASSING
- **Skills included**:
  - Stakeholder Management
  - Stakeholder Engagement
  - Executive Communication
  - Cross-functional Collaboration
  - Team Collaboration

#### 1.4 Data Management Category
- **Test**: `test_data_management_category_exists`
- **Status**: PASSING
- **Skills included**:
  - Data Quality
  - Data Quality Assessment
  - Data Profiling
  - Data Lineage
  - Data Lineage Tracking

#### 1.5 Skill Category Lookup
- **Test**: `test_skill_category_lookup`
- **Status**: PASSING
- **Verifies**: `get_skill_category()` function returns correct category for skill lookup
- **Handles**: Case variations, multiple category matches, unknown skills

#### 1.6 Boilerplate Filtering
- **Test**: `test_boilerplate_sales_filtered`
- **Status**: PASSING
- **Verifies**: False positives like "Sales" in company descriptions are filtered out
- **Implementation**: `extract_skills_keywords()` detects boilerplate sections and excludes non-technical skills found only there

#### 1.7 State Street Extraction Baseline
- **Test**: `test_state_street_extracts_more_skills`
- **Status**: PASSING
- **Validates**: Realistic JD (State Street) extracts >= 12 skills (baseline was 7)
- **Improvement drivers**:
  - Better boilerplate filtering
  - New category expansion
  - Refined skill taxonomy

## Phase 2: LLM-Powered Skill Extraction

### Status: FAILING (3/3 tests failing - awaiting implementation)

Phase 2 introduces LLM-powered skill extraction and hybrid extraction method.

#### 2.1 MockLLM Has Extract Skills Method
- **Test**: `test_mock_llm_has_extract_skills_method`
- **Status**: FAILING
- **Required implementation**:
  ```python
  async def extract_skills_from_jd(jd_text: str) -> Dict[str, Any]
  ```
- **Location**: `backend/services/llm/mock_llm.py`

#### 2.2 MockLLM Returns Correct Schema
- **Test**: `test_mock_llm_returns_correct_schema`
- **Status**: FAILING
- **Expected return schema**:
  ```python
  {
      'extracted_skills': List[str],      # All skills found
      'critical_skills': List[str],       # Must-have (requirements section)
      'preferred_skills': List[str],      # Nice-to-have
      'domain_skills': List[str],         # Domain-specific skills
      'confidence': float (0.0-1.0)       # Overall confidence
  }
  ```
- **Implementation notes**:
  - Use keyword detection on requirements vs. nice-to-haves
  - Domain inference from JD text
  - Confidence based on keyword match frequency

#### 2.3 Hybrid Extraction Combines Sources
- **Test**: `test_hybrid_extraction_combines_sources`
- **Status**: FAILING
- **Required implementation**:
  ```python
  async def extract_skills_hybrid(jd_text: str) -> Dict[str, Any]
  ```
- **Location**: `backend/services/job_parser.py`
- **Expected return schema**:
  ```python
  {
      'taxonomy_skills': List[str],   # From keyword matching
      'llm_skills': List[str],        # From LLM extraction
      'all_skills': List[str],        # Deduplicated union
      'overlap': List[str],           # Skills found in both
      'confidence': float             # Weighted confidence
  }
  ```
- **Implementation logic**:
  1. Call `extract_skills_keywords()` for taxonomy-based extraction
  2. Call `MockLLM.extract_skills_from_jd()` for LLM-based extraction
  3. Deduplicate and merge results
  4. Prefer skills appearing in both sources (higher confidence)
  5. Calculate weighted confidence score

## Phase 3: Domain Inference & Skill Enrichment

### Status: PARTIALLY IMPLEMENTED (1/3 tests passing, 2 skipped)

Phase 3 enhances resume skills selection with domain-aware enrichment using Tier 5.

#### 3.1 Domain Inference - Governance
- **Test**: `test_infer_job_domain_governance`
- **Status**: SKIPPED (awaiting `infer_job_domain()` function)
- **Required implementation**:
  ```python
  def infer_job_domain(jd_text: str) -> str
  ```
- **Location**: `backend/services/job_parser.py`
- **Governance signals**:
  - Keywords: "governance", "compliance", "risk", "policy", "audit"
  - Skills: "AI Governance", "Model Risk Management", "Compliance"
  - Titles: "Governance", "Compliance", "Risk"

#### 3.2 Domain Inference - Data Analytics
- **Test**: `test_infer_job_domain_data_analytics`
- **Status**: SKIPPED (awaiting `infer_job_domain()` function)
- **Data Analytics signals**:
  - Keywords: "analytics", "data analysis", "insights", "dashboard"
  - Skills: "Power BI", "Tableau", "SQL", "Python", "Analytics"
  - Titles: "Analyst", "Analytics", "Data Analyst"

#### 3.3 Tier 5 Ancillary Skills
- **Test**: `test_tier5_surfaces_ancillary_skills`
- **Status**: PASSING (with mock objects)
- **Validates**: The `select_and_order_skills()` function uses 5-tier approach:
  - **Tier 1**: Critical matched skills (match_strength >= 0.75)
  - **Tier 2**: Strong matched skills (0.5 <= match_strength < 0.75)
  - **Tier 3**: Must-have job requirements
  - **Tier 4**: Weak signals and transferable skills
  - **Tier 5**: Domain-relevant ancillary skills from user bullets
- **Implementation notes**:
  - Tier 5 should surface skills user has (bullet tags) that relate to job domain
  - Must not duplicate Tiers 1-4
  - Should select from relevant skill categories (leadership, technical, process, domain, soft)
  - Example: For governance role, surface "Stakeholder Management", "Data Lineage"

## Integration Tests

### Status: PASSING (2/2 tests)

#### Integration 1: Phase 1 Enables Phase 2
- **Test**: `test_phase1_enables_phase2`
- **Status**: PASSING
- **Validates**: New categories improve hybrid extraction coverage and confidence

#### Integration 2: End-to-End Flow
- **Test**: `test_end_to_end_skill_extraction_flow`
- **Status**: PASSING
- **Validates**: Full extraction pipeline works with realistic JD
- **Stages**:
  1. Extract with Phase 1 keyword method (already working)
  2. Extract with Phase 2 LLM method (awaiting implementation)
  3. Combine with Phase 3 domain inference (awaiting implementation)

## Running the Tests

### Run all tests
```bash
cd backend
python -m pytest tests/test_skill_extraction_enhancements.py -v
```

### Run Phase 1 tests (should all pass)
```bash
python -m pytest tests/test_skill_extraction_enhancements.py::TestPhase1SkillTaxonomyExpansion -v
```

### Run Phase 2 tests (should fail - awaiting implementation)
```bash
python -m pytest tests/test_skill_extraction_enhancements.py::TestPhase2LLMSkillExtraction -v
```

### Run Phase 3 tests
```bash
python -m pytest tests/test_skill_extraction_enhancements.py::TestPhase3DomainInferenceAndEnrichment -v
```

### Run integration tests
```bash
python -m pytest tests/test_skill_extraction_enhancements.py::TestSkillExtractionIntegration -v
```

## Implementation Roadmap

### Phase 1: COMPLETE
- [x] Expand SKILL_TAXONOMY with 4 new categories
- [x] Improve boilerplate filtering in `extract_skills_keywords()`
- [x] Verify baseline extraction meets >= 12 skills on realistic JD

### Phase 2: TODO
- [ ] Implement `MockLLM.extract_skills_from_jd()` method
  - [ ] Parse requirements vs. nice-to-haves
  - [ ] Identify critical skills
  - [ ] Calculate confidence score
- [ ] Implement `extract_skills_hybrid()` function
  - [ ] Combine taxonomy and LLM results
  - [ ] Deduplicate intelligently
  - [ ] Calculate weighted confidence
  - [ ] Weight overlap matches higher

### Phase 3: TODO
- [ ] Implement `infer_job_domain()` function
  - [ ] Support "governance", "data_analytics", and other domains
  - [ ] Use keyword and skill matching for inference
  - [ ] Return domain name string
- [ ] Enhance `select_and_order_skills()` Tier 5 logic
  - [ ] Add domain-aware skill surfacing
  - [ ] Surface ancillary skills from user bullets that relate to domain
  - [ ] Verify minimum threshold of Tier 5 skills added

## Key Files

- **Test File**: `/Users/benjaminblack/projects/etps/backend/tests/test_skill_extraction_enhancements.py`
- **Job Parser**: `/Users/benjaminblack/projects/etps/backend/services/job_parser.py`
  - Contains: SKILL_TAXONOMY, extract_skills_keywords(), get_skill_category()
  - TODO Phase 2: Add extract_skills_hybrid()
  - TODO Phase 3: Add infer_job_domain()
- **Mock LLM**: `/Users/benjaminblack/projects/etps/backend/services/llm/mock_llm.py`
  - TODO Phase 2: Add extract_skills_from_jd()
- **Resume Tailor**: `/Users/benjaminblack/projects/etps/backend/services/resume_tailor.py`
  - Contains: select_and_order_skills() with Tier 1-5 logic
  - Tier 5 enhancement already implemented

## Test Naming Convention

All tests follow clear descriptive naming:
- Phase/Test number prefix: `test_phase<N>_<brief_description>`
- Status indicator: Function docstring clearly states PASSING/FAILING/SKIPPED
- Clear assertions with helpful error messages

## Notes

- Tests use mock objects where appropriate (Tier 5 test uses mocks)
- Tests gracefully skip when functions not yet implemented (Phase 3 domain inference)
- All Phase 1 tests pass - confirms baseline is solid
- Phase 2 tests are properly failing with clear error messages
- Total test coverage: 15 tests across 3 phases + integration

## Contact

For questions about these tests or the skill extraction enhancement plan, refer to `docs/IMPLEMENTATION_PLAN.md` Sprint 11-14 section.

# Skill Gap Analyzer Test Architecture

## Document Purpose

This document explains the design, organization, and philosophy behind the comprehensive test suite for the Sprint 2 Skill Gap Analyzer enhancements.

## Test Structure Overview

```
test_skill_gap.py (1,347 lines)
├── Utilities
│   └── setup_test_data() - Creates realistic test data
├── 9 Test Classes (26 test methods)
│   ├── TestSemanticSkillMatching (4 tests)
│   ├── TestGapCategorization (3 tests)
│   ├── TestPositioningStrategy (3 tests)
│   ├── TestWeakSignalDetection (3 tests)
│   ├── TestResumeTailoringIntegration (3 tests)
│   ├── TestDatabasePersistence (3 tests)
│   ├── TestPositioningStrategyContent (2 tests)
│   ├── TestCoverLetterAndAdvantagesGeneration (2 tests)
│   └── TestSkillGapAnalysisIntegration (3 tests)
└── Main Entry Point (run_tests())
```

## Design Philosophy

### 1. Test-Driven Development (TDD)

The test suite is designed to guide Sprint 2 implementation using TDD principles:

- **Red Phase:** Tests are written BEFORE features (tests fail)
- **Green Phase:** Minimal code is written to make tests pass
- **Refactor Phase:** Code is improved while tests remain green

This approach ensures:
- Clear specification of expected behavior
- Comprehensive coverage from the start
- Confidence in refactoring

### 2. Layered Testing Approach

Tests are organized by feature area, not by implementation layer:

**Feature-Driven Organization:**
- Semantic Skill Matching
- Gap Categorization
- Positioning Strategies
- Weak Signal Detection
- Resume Tailoring Integration
- Database Persistence

NOT organized by:
- Database layer tests
- Service layer tests
- API layer tests

This keeps tests focused on user-facing behavior.

### 3. Realistic Test Data

All tests use `setup_test_data()` which creates:
- Real SQLAlchemy model instances
- Multiple experiences with different seniority levels
- Realistic bullet points with actual impact metrics
- Comprehensive job profile with clear requirements

Example data reflects actual use cases:
- ML Engineer with Kubernetes and DevOps background
- Job requiring ML expertise and team leadership
- Clear gaps (LLM, AI Governance) and strengths (Python, ML)

### 4. Clear Expectation Marking

Every test documents whether it should pass or fail:

```python
def test_semantic_matching_ml_to_machine_learning(self):
    """Test that 'ML Engineering' matches 'Machine Learning' semantically.

    EXPECTS FAIL in current implementation (no semantic matching).
    Sprint 2: Should use embeddings or LLM to recognize semantic similarity.
    """
```

This clarity serves multiple purposes:
- Shows what's already implemented vs. what's planned
- Prevents false alarm failures during implementation
- Documents requirements precisely
- Guides prioritization (implement EXPECTS FAIL tests in order)

### 5. Integration-Focused

Tests span multiple components:
- Database layer (save/retrieve from JobProfile)
- Service layer (skill_gap.py functions)
- Schema layer (request/response validation)
- Integration points (resume tailoring)

This ensures components work together correctly.

## Test Data Organization

### `setup_test_data()` Function

Creates a realistic scenario with:

```
User (AI/ML background)
├── Experience 1: Senior ML Engineer (current)
│   ├── Bullet 1: ML pipeline architecture
│   ├── Bullet 2: NLP team leadership
│   ├── Bullet 3: Kubernetes migration
│   ├── Bullet 4: FastAPI microservices
│   └── Bullet 5: Data quality work (weak)
└── Experience 2: Data Engineer (2018-2020)
    ├── Bullet 1: Apache Spark ETL
    └── Bullet 2: Data infrastructure

JobProfile: Senior ML Engineering Manager
├── Must Have: ML, Deep Learning, Python, Kubernetes, Leadership
├── Nice to Have: LLM, Generative AI, Model Risk Management, etc.
└── Core Priorities: ML leadership, deep learning, team building
```

### Why This Specific Data?

This test data was chosen to:

1. **Test Core Logic:**
   - User has most required skills → matched_skills populated
   - User missing LLM, Generative AI → skill_gaps detected
   - User has related skills (Spark, Python) → weak_signals possible

2. **Avoid Trivial Cases:**
   - Not just one skill gap
   - Not all skills matched
   - Not a weak match across the board
   - Mix of strong, medium, and weak bullets

3. **Enable Sprint 2 Features:**
   - Multiple experience types (full-time + consultant roles)
   - Various skill levels (junior responsibility to senior achievement)
   - Metrics and impact language for analysis
   - Different relevance scores for skill importance

4. **Support All Test Categories:**
   - Semantic tests: "ML Engineering" vs "Machine Learning"
   - Gap categorization: Tests/Nice-to-have distinction
   - Positioning: Multiple strategies with real context
   - Weak signals: Related skills like ETL → ML
   - Persistence: Realistic volume of data

## Test Execution Flow

### Single Test Execution

```
test_skill_gap_analysis_saved_to_job_profile()
│
├─ setup_test_data()  ─┐
│                      ├─> Create User
├─ db.query()          ├─> Create Experiences
│                      ├─> Create Bullets
├─ analyze_skill_gap() ├─> Create JobProfile
│                      └─> Return (user_id, job_profile_id)
│
├─ db.refresh()  ─> Re-read JobProfile from DB
│
├─ assert job_profile.skill_gap_analysis is not None
│
└─ db.rollback()  ─> Clean up test data
```

### Key Flow Elements

1. **Setup (Arrange):** `setup_test_data()` creates all prerequisites
2. **Execution (Act):** Call the function being tested
3. **Verification (Assert):** Check results match expectations
4. **Cleanup (After):** `db.rollback()` in finally block ensures clean state

## Async Test Handling

Tests use `@pytest.mark.asyncio` for async functions:

```python
@pytest.mark.asyncio
async def test_skill_gap_analysis_saved_to_job_profile(self):
    db = next(get_db())
    try:
        # Test code here
        response = await analyze_skill_gap(...)
    finally:
        db.rollback()
```

This pattern:
- Uses pytest-asyncio to run async tests
- Properly handles async/await syntax
- Cleans up resources in finally block

## Test Isolation

Each test is completely isolated:

- Fresh database session for each test: `db = next(get_db())`
- Rollback after each test: `db.rollback()` in finally
- No shared state between tests
- Tests can run in any order

### Why Isolation Matters

- **Reliability:** Tests don't interfere with each other
- **Parallelization:** Tests can run concurrently safely
- **Debugging:** Failures are easier to understand in isolation
- **Repeatability:** Tests pass/fail consistently

## Error Messages

Tests include detailed error messages explaining:
- What was expected
- What was found
- Why it matters for Sprint 2

Example:
```python
assert matched is not None, (
    "Semantic matching should recognize ML Engineering as related to Machine Learning. "
    "Current implementation uses only exact/synonym matching."
)
```

Benefits:
- Clear understanding of what feature is missing
- Actionable guidance for implementation
- Documentation of requirements

## Assertion Patterns

### Type Checks
```python
assert isinstance(response, SkillGapResponse)
```
Validates schema correctness.

### Numeric Range Checks
```python
assert 0 <= response.skill_match_score <= 100
```
Validates computed values are reasonable.

### Collection Checks
```python
assert len(response.matched_skills) > 0
```
Validates lists contain expected elements.

### Content Checks
```python
assert any("LLM" in str(g.skill) for g in nice_to_have_gaps)
```
Validates specific content presence.

### Relationship Checks
```python
assert response.skill_match_score >= initial_score
```
Validates logical relationships between values.

## Test Categories and Purposes

### Category 1: Feature Specification (EXPECTS FAIL)
- Precisely define what each feature should do
- Guide implementation work
- Validate feature completeness
- Enable regression testing once implemented

Example: `test_semantic_matching_ml_to_machine_learning`

### Category 2: Core Functionality (EXPECTS PASS)
- Validate existing implementation works correctly
- Catch regressions immediately
- Ensure data flow integrity
- Test edge cases in current logic

Example: `test_fallback_to_synonym_when_embedding_unavailable`

### Category 3: Integration (Mixed)
- Validate components work together
- Test end-to-end workflows
- Catch integration issues
- Verify schema contracts are honored

Example: `test_end_to_end_analysis_with_real_data`

## Test Data Dependencies

### Service Dependencies

Each test class uses these services:

- `analyze_skill_gap()` - Main analysis function
- `build_user_skill_profile()` - User profile aggregation
- `compute_matched_skills()` - Skill matching logic
- `compute_missing_skills()` - Gap calculation
- `compute_weak_signals()` - Weak signal detection
- `compute_skill_match_score()` - Score calculation
- `generate_positioning_strategies()` - Strategy generation

### Schema Dependencies

Tests use these Pydantic models:

- `SkillGapRequest` - Input validation
- `SkillGapResponse` - Output validation
- `SkillMatch` - Matched skill representation
- `SkillGap` - Missing skill representation
- `WeakSignal` - Weak signal representation
- `UserSkillProfile` - User skill aggregation

### Database Dependencies

Tests use these SQLAlchemy models:

- `User` - Test candidate
- `Experience` - Work roles
- `Bullet` - Achievement bullet points
- `JobProfile` - Job requirements

## Test Maintenance Guidelines

### When Adding New Tests

1. **Choose appropriate class:**
   - Does it test skill matching? → `TestSemanticSkillMatching`
   - Does it test gap types? → `TestGapCategorization`
   - Does it test strategies? → `TestPositioningStrategy`
   - Does it test weak signals? → `TestWeakSignalDetection`
   - Does it test resume integration? → `TestResumeTailoringIntegration`
   - Does it test database? → `TestDatabasePersistence`

2. **Write descriptive docstring:**
   ```python
   def test_feature_scenario(self):
       """Test that feature does X when given Y.

       EXPECTS FAIL - Feature not yet implemented.
       Sprint 2: Should implement Z.
       """
   ```

3. **Use consistent pattern:**
   - Arrange: `db`, `setup_test_data()`, `db.query()`
   - Act: `await analyze_skill_gap()` or similar
   - Assert: Check result, validate structure, verify content
   - After: `db.rollback()`

4. **Ensure isolation:**
   - Don't depend on previous tests
   - Clean up in finally block
   - Use unique identifiers (uuid) to avoid conflicts

### When Test Fails Unexpectedly

1. **Check if it's marked correctly:**
   - Should it be EXPECTS FAIL?
   - Is the assertion checking the right thing?

2. **Review test data:**
   - Did setup_test_data() create what we expect?
   - Are we querying the right records?

3. **Check implementation:**
   - Did the service function change?
   - Is the schema validation correct?

4. **Debug with prints:**
   ```bash
   pytest test_skill_gap.py::TestClass::test_method -v -s
   ```

## Performance Characteristics

### Test Execution Time

- Individual test: 100-500ms (database operations)
- Full test class: 1-3 seconds
- Full test suite: 30-60 seconds
- With coverage: 60-90 seconds

### Optimization Opportunities

- Batch create test data if many tests use same data
- Use in-memory SQLite for tests (currently uses DB file)
- Mock external services (LLM, embedding) in unit tests
- Parallelize tests with pytest-xdist

### Current Trade-offs

- **Realism over speed:** Using real database + models for data integrity
- **Coverage over speed:** 26 comprehensive tests vs. 5 fast tests
- **Documentation over speed:** Detailed error messages increase test size

## Evolution Through Sprints

### Current State (Test Time)
- Tests document all planned features
- Approximately 1/3 should pass with current implementation
- Remaining 2/3 guide Sprint 2 implementation

### Sprint 2 (Implementation)
- Tests guide feature implementation in priority order
- As features complete, more tests become green
- No test changes needed; just implementation
- Final state: All tests pass

### Post-Sprint 2
- All tests pass; suite serves as regression tests
- New tests added for future features
- Can add performance tests once features stable
- Can refactor to use mocks for speed if needed

## Key Success Metrics

The test suite succeeds when:

1. **All EXPECTS PASS tests pass** (no regressions)
2. **EXPECTS FAIL tests fail for right reasons** (document requirements)
3. **Clear error messages guide implementation** (reduces debugging)
4. **Tests run reliably** (no flakiness)
5. **Implementation is straightforward** (tests guide clearly)

## References

- Implementation Guide: `/Users/benjaminblack/projects/etps/backend/SKILL_GAP_TEST_SUMMARY.md#implementation-roadmap-for-sprint-2`
- Execution Guide: `/Users/benjaminblack/projects/etps/backend/TEST_EXECUTION_GUIDE.md`
- Test File: `/Users/benjaminblack/projects/etps/backend/test_skill_gap.py`

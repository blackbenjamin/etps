# Skill Gap Analyzer Test Execution Guide

## Quick Start

```bash
cd /Users/benjaminblack/projects/etps/backend
pytest test_skill_gap.py -v
```

## Test Statistics

- **Total Tests:** 26 methods across 9 classes
- **Lines of Code:** 1,347
- **Expected to Pass:** ~8-10 tests
- **Expected to Fail:** ~16-18 tests (documenting Sprint 2 features)

## Test Execution Patterns

### Run All Tests
```bash
pytest test_skill_gap.py -v
```

### Run Only Passing Tests (Base Implementation)
```bash
pytest test_skill_gap.py -v -k "fallback or multiple_candidate or end_to_end or comprehensive or junior or cover_letter or advantages"
```

### Run Only Failing Tests (Sprint 2 Features)
```bash
pytest test_skill_gap.py -v -x  # Stop at first failure
```

### Run Specific Test Class
```bash
# Semantic Matching Tests
pytest test_skill_gap.py::TestSemanticSkillMatching -v

# Gap Categorization Tests
pytest test_skill_gap.py::TestGapCategorization -v

# Positioning Strategy Tests
pytest test_skill_gap.py::TestPositioningStrategy -v

# Weak Signal Detection Tests
pytest test_skill_gap.py::TestWeakSignalDetection -v

# Resume Tailoring Integration Tests
pytest test_skill_gap.py::TestResumeTailoringIntegration -v

# Database Persistence Tests
pytest test_skill_gap.py::TestDatabasePersistence -v

# Positioning Strategy Content Tests
pytest test_skill_gap.py::TestPositioningStrategyContent -v

# Cover Letter and Advantages Tests
pytest test_skill_gap.py::TestCoverLetterAndAdvantagesGeneration -v

# Integration Tests
pytest test_skill_gap.py::TestSkillGapAnalysisIntegration -v
```

### Run Single Test
```bash
pytest test_skill_gap.py::TestSemanticSkillMatching::test_fallback_to_synonym_when_embedding_unavailable -v
```

### Run with Output Capture
```bash
# Show print statements
pytest test_skill_gap.py -v -s

# Show local variables on failure
pytest test_skill_gap.py -v -l

# Show tracebacks
pytest test_skill_gap.py -v --tb=short
```

### Run with Coverage
```bash
pytest test_skill_gap.py --cov=services.skill_gap --cov-report=html
open htmlcov/index.html
```

### Run Specific Tests by Pattern
```bash
# All tests with "semantic" in name
pytest test_skill_gap.py -k "semantic" -v

# All tests with "strategy" in name
pytest test_skill_gap.py -k "strategy" -v

# All tests with "database" in name
pytest test_skill_gap.py -k "database" -v

# All tests with "integration" in name
pytest test_skill_gap.py -k "integration" -v
```

## Test Categories by Status

### Currently Passing (Base Implementation)
1. `TestSemanticSkillMatching::test_fallback_to_synonym_when_embedding_unavailable`
2. `TestSemanticSkillMatching::test_multiple_candidate_skills_returns_best_match`
3. `TestWeakSignalDetection::test_weak_signal_evidence_includes_actual_bullet_text`
4. `TestSkillGapAnalysisIntegration::test_end_to_end_analysis_with_real_data`
5. `TestSkillGapAnalysisIntegration::test_analysis_with_comprehensive_user_profile`
6. `TestSkillGapAnalysisIntegration::test_analysis_with_junior_candidate`
7. `TestCoverLetterAndAdvantagesGeneration::test_cover_letter_hooks_reference_matched_skills`
8. `TestCoverLetterAndAdvantagesGeneration::test_user_advantages_drawn_from_profile`

### Documenting Sprint 2 Features (Expected to Fail)
1. `TestSemanticSkillMatching::test_semantic_matching_ml_to_machine_learning`
2. `TestSemanticSkillMatching::test_similarity_threshold_respects_config`
3. `TestGapCategorization::test_critical_skills_from_requirements_section`
4. `TestGapCategorization::test_nice_to_have_skills_categorized_correctly`
5. `TestGapCategorization::test_llm_based_categorization_various_jd_structures`
6. `TestPositioningStrategy::test_strategies_reference_user_actual_skills`
7. `TestPositioningStrategy::test_strategies_align_with_job_priorities`
8. `TestPositioningStrategy::test_critical_gaps_get_mitigation_strategies`
9. `TestWeakSignalDetection::test_semantic_detection_finds_related_skills`
10. `TestWeakSignalDetection::test_weak_signals_ranked_by_similarity_score`
11. `TestResumeTailoringIntegration::test_skill_gap_called_during_tailoring`
12. `TestResumeTailoringIntegration::test_bullet_selection_uses_prioritize_tags_guidance`
13. `TestResumeTailoringIntegration::test_skill_gap_summary_included_in_response`
14. `TestDatabasePersistence::test_skill_gap_analysis_saved_to_job_profile`
15. `TestDatabasePersistence::test_cache_retrieval_works`
16. `TestDatabasePersistence::test_cache_invalidation_on_user_profile_change`
17. `TestPositioningStrategyContent::test_strategies_are_actionable_not_generic`
18. `TestPositioningStrategyContent::test_mitigation_strategies_address_specific_gaps`

## Understanding Test Failures

### EXPECTS FAIL Tests
When a test marked "EXPECTS FAIL" fails, that's expected and correct. These tests:
- Document Sprint 2 features not yet implemented
- Will guide implementation work
- Should become green as features are built

Example failure message:
```
AssertionError: Semantic matching should recognize ML Engineering as related to Machine Learning.
Current implementation uses only exact/synonym matching.
```

### EXPECTS PASS Tests
When a test marked "EXPECTS PASS" fails, something is broken. These tests:
- Validate core functionality that should work
- Help catch regressions
- Should always pass

## Running Tests in CI/CD

### GitHub Actions Example
```yaml
- name: Run Skill Gap Tests
  run: |
    cd backend
    pytest test_skill_gap.py -v --tb=short

- name: Collect Sprint 2 Status
  run: |
    pytest test_skill_gap.py --co -q | grep "EXPECTS FAIL" | wc -l
```

### Pre-commit Hook
```bash
#!/bin/bash
cd backend
pytest test_skill_gap.py -k "not FAIL" -q || exit 1
```

## Test Debugging

### Print Debug Info
```bash
pytest test_skill_gap.py::TestSemanticSkillMatching::test_semantic_matching_ml_to_machine_learning -v -s
```

### Drop into Debugger
```bash
pytest test_skill_gap.py --pdb -k "test_semantic_matching"
```

### Inspect Database State
The tests create temporary database records. To inspect:
```python
# In your test, add:
db.commit()  # Ensure changes are persisted
print(f"Created user: {user.id}")
print(f"Created job_profile: {job_profile.id}")
```

### Performance Profiling
```bash
pytest test_skill_gap.py --durations=10
```

## Integration with Development Workflow

### While Implementing Sprint 2 Features

1. **Before starting a feature:**
   ```bash
   pytest test_skill_gap.py -v | grep "XFAIL\|FAILED"
   ```

2. **While implementing:**
   ```bash
   pytest test_skill_gap.py::TestYourFeature -v --tb=short
   ```

3. **After completing a feature:**
   ```bash
   pytest test_skill_gap.py -v
   # Verify feature tests now pass
   # Verify no regressions in passing tests
   ```

### Progress Tracking

Track Sprint 2 implementation by monitoring passing tests:

```bash
# Count currently passing tests
pytest test_skill_gap.py --co -q | grep "test_" | wc -l  # Total
pytest test_skill_gap.py -v 2>&1 | grep PASSED | wc -l   # Currently passing
```

## Common Issues and Solutions

### Issue: Import Errors
```
ModuleNotFoundError: No module named 'services.skill_gap'
```
**Solution:** Ensure working directory is `/Users/benjaminblack/projects/etps/backend`

### Issue: Database Errors
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```
**Solution:** Test creates temporary DB. Ensure db/ directory exists and is writable.

### Issue: Async Errors
```
RuntimeError: Event loop is closed
```
**Solution:** Tests use `@pytest.mark.asyncio`. Ensure pytest-asyncio is installed.

### Issue: Timeout in Tests
```
TimeoutError: Test exceeded timeout of X seconds
```
**Solution:** Some tests create realistic data. May be slow on first run. Adjust timeout with:
```bash
pytest test_skill_gap.py --timeout=60 -v
```

## Test Maintenance

### Adding New Tests
When adding new tests for Sprint 2 features:

1. Add to appropriate test class
2. Use proper naming: `test_<feature>_<scenario>`
3. Add docstring explaining expected behavior
4. Mark with `(EXPECTS FAIL)` if not yet implemented
5. Use same patterns as existing tests

### Updating Existing Tests
If base implementation changes:

1. Update both `setup_test_data()` and test methods
2. Ensure test isolation (clean DB between tests)
3. Verify no hardcoded assumptions
4. Run full suite to check for regressions

## Performance Notes

- Full test suite takes ~30-60 seconds
- Creating test data (experiences, bullets) takes ~5-10 seconds
- Database queries should be cached
- Consider parallelization: `pytest -n auto`

## References

- Test file: `/Users/benjaminblack/projects/etps/backend/test_skill_gap.py`
- Summary: `/Users/benjaminblack/projects/etps/backend/SKILL_GAP_TEST_SUMMARY.md`
- Service: `/Users/benjaminblack/projects/etps/backend/services/skill_gap.py`
- Schemas: `/Users/benjaminblack/projects/etps/backend/schemas/skill_gap.py`

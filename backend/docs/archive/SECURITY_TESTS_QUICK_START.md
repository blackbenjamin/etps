# Security Tests Quick Start Guide

## Running the Tests

### Run All Tests
```bash
cd /Users/benjaminblack/projects/etps/backend
python -m pytest tests/test_security.py -v
```

### Run Specific Test Category
```bash
# CORS tests
python -m pytest tests/test_security.py::TestCORSConfiguration -v

# SSRF prevention tests
python -m pytest tests/test_security.py::TestSSRFPrevention -v

# Error sanitization tests
python -m pytest tests/test_security.py::TestErrorSanitization -v

# Health check tests
python -m pytest tests/test_security.py::TestHealthCheck -v
```

### Run a Single Test
```bash
python -m pytest tests/test_security.py::TestSSRFPrevention::test_block_private_ip_10_0_0_0_8 -v
```

### Run with Code Coverage
```bash
python -m pytest tests/test_security.py --cov=services --cov-report=html
```

## Understanding the Results

### Current Status: 36 passed, 19 skipped

**Passing Tests (36):**
- All SSRF prevention tests (9/9)
- All error sanitization tests (5/5)
- All security edge cases (6/6)
- Most CORS tests (5/6)
- Most health check tests (4/8)
- Most integration tests (4/5)
- Request body size limits (2/5)

**Skipped Tests (19):**
- Rate limiting (4) - implementation pending
- Security headers (4) - middleware not yet added
- Health endpoints (4) - future Kubernetes support
- Configuration (3) - code inspection tests
- Boundary tests (3) - require full request setup
- Rate limit integration (1) - depends on rate limiting

## What's Tested

### Already Passing (Implemented)
1. **SSRF Prevention** - Private IP blocking, URL scheme validation
2. **Error Sanitization** - No stack traces or file paths in errors
3. **Request Limits** - Oversized payloads rejected
4. **CORS** - Dev origins allowed, unauthorized origins blocked
5. **Health Check** - Version and status endpoints working

### Needs Implementation
1. **Rate Limiting** - 10 req/min (POST), 60 req/min (GET)
2. **Security Headers** - CSP, X-Frame-Options, X-Content-Type-Options
3. **Production CORS** - https://etps.benjaminblack.ai origin
4. **Health Endpoints** - /health/liveness and /health/readiness

## Key Test Files

**Main Test File:**
- `/Users/benjaminblack/projects/etps/backend/tests/test_security.py` (761 lines, 55 tests)

**Documentation:**
- `/Users/benjaminblack/projects/etps/backend/tests/TEST_SECURITY_README.md` - Detailed reference
- `/Users/benjaminblack/projects/etps/backend/tests/SECURITY_TESTS_QUICK_START.md` - This file

## Common Issues & Solutions

### Tests Won't Run
```bash
# Make sure you're in the backend directory
cd /Users/benjaminblack/projects/etps/backend

# Install dependencies
pip install pytest fastapi httpx
```

### Import Errors
```bash
# Make sure PYTHONPATH includes backend directory
export PYTHONPATH=/Users/benjaminblack/projects/etps/backend:$PYTHONPATH
```

### Specific Test Fails
- Check if it's marked SKIP - those require implementation
- Read the test docstring for what's being tested
- Look at the assertion error message for details

## Test Anatomy

Each test follows this pattern:

```python
def test_feature_scenario(self, client):
    """One-line description of what's tested.
    
    Longer explanation if needed.
    """
    # Arrange: Set up test data
    test_value = "some input"
    
    # Act: Call the code under test
    response = client.post("/endpoint", json={"field": test_value})
    
    # Assert: Verify the expected outcome
    assert response.status_code == 200
    assert "expected" in response.json()
```

## For Sprint 13 Implementation

When implementing a feature:

1. Find the relevant skipped test
2. Implement the feature until the test passes
3. Remove the `pytest.skip()` call
4. Run the test to verify it passes
5. Update the test count in documentation

Example:
```python
# Before (skipped)
def test_rate_limit_429_response_with_retry_after_header(self, client):
    pytest.skip("Rate limiting middleware not yet implemented")

# After (implemented)
def test_rate_limit_429_response_with_retry_after_header(self, client):
    # Make requests to hit the limit
    # Verify 429 response with Retry-After header
    assert response.status_code == 429
    assert "retry-after" in response.headers
```

## Integration with CI/CD

Add to your CI pipeline:
```yaml
- name: Run Security Tests
  run: |
    cd backend
    python -m pytest tests/test_security.py -v --tb=short
    python -m pytest tests/test_security.py --cov=services
```

## Test Categories & Count

| Category | Total | Passing | Skipped | Status |
|----------|-------|---------|---------|--------|
| Rate Limiting | 4 | 0 | 4 | Pending |
| CORS | 6 | 5 | 0 | 1 fix needed |
| SSRF | 9 | 9 | 0 | Complete |
| Body Limits | 5 | 2 | 3 | Partial |
| Error San. | 5 | 5 | 0 | Complete |
| Headers | 4 | 0 | 4 | Pending |
| Health | 8 | 4 | 4 | Partial |
| Edge Cases | 6 | 6 | 0 | Complete |
| Integration | 5 | 4 | 1 | Partial |
| Config | 3 | 0 | 3 | Pending |
| **TOTAL** | **55** | **36** | **19** | **67% pass** |

## Next Steps

1. Review the skipped tests to understand what's needed
2. Implement rate limiting middleware
3. Add security headers middleware
4. Add production origin to CORS
5. Rerun tests - target is 55 passing, 0 skipped

## Questions?

Refer to:
- Sprint 13 requirements: `/Users/benjaminblack/projects/etps/docs/IMPLEMENTATION_PLAN.md`
- Full test docs: `TEST_SECURITY_README.md`
- Individual test docstrings in `test_security.py`

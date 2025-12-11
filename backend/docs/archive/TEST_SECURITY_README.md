# Sprint 13: Portfolio Security Hardening - Test Suite

## Overview

Comprehensive test suite for Sprint 13 security requirements. Tests validate that the ETPS backend is hardened for safe public portfolio deployment.

**Test File:** `/Users/benjaminblack/projects/etps/backend/tests/test_security.py`

**Current Status:** 36 passing, 19 skipped

## Test Coverage

### 1. Rate Limiting Tests (4 tests)
Tests that API endpoints enforce request rate limits per IP address.

**Status:** Skipped (implementation pending)

**Required Implementation:**
- Generation endpoints (POST): 10 requests/minute per IP
- Read endpoints (GET): 60 requests/minute per IP
- Return HTTP 429 with `Retry-After` header when exceeded
- Track limits separately per IP address

**Tests:**
- `test_rate_limit_generation_endpoint_10_per_minute` - Validates 10 req/min limit for POST endpoints
- `test_rate_limit_read_endpoint_60_per_minute` - Validates 60 req/min limit for GET endpoints
- `test_rate_limit_429_response_with_retry_after_header` - Validates 429 response with header
- `test_rate_limit_separate_per_ip` - Validates per-IP tracking

### 2. CORS Configuration Tests (6 tests)
Tests that Cross-Origin Resource Sharing is properly configured.

**Status:** 5 passing, 1 needs implementation

**Configuration:**
```
Allowed Origins:
- http://localhost:3000      (dev, currently working)
- http://localhost:3001      (dev alternate, currently working)
- http://127.0.0.1:3000      (dev alternative, currently working)
- https://etps.benjaminblack.ai  (production, needs to be added)
```

**Tests:**
- `test_production_origin_allowed` - FAIL: Production origin not yet in allow list
- `test_localhost_3000_dev_allowed` - PASS: Dev environment supported
- `test_localhost_3001_dev_allowed` - PASS: Alternate dev port supported
- `test_unauthorized_origin_rejected` - PASS: Malicious origins blocked
- `test_credentials_allowed_with_cors` - PASS: CORS credentials configured
- `test_methods_allowed_in_cors_header` - PASS: HTTP methods in CORS headers

**Implementation Needed:**
```python
# In main.py, update CORS configuration:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://etps.benjaminblack.ai",  # Add this for production
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    ...
)
```

### 3. SSRF Prevention Tests (9 tests)
Tests that prevent Server-Side Request Forgery attacks by blocking internal IP access.

**Status:** All passing

**Protected IP Ranges:**
- 10.0.0.0/8 (private)
- 172.16.0.0/12 (private)
- 192.168.0.0/16 (private)
- 127.0.0.1/8 (loopback)
- 169.254.169.254 (AWS/GCP/Azure metadata endpoint)

**Tests:**
- `test_block_private_ip_10_0_0_0_8` - PASS: Blocks 10.0.0.0/8 range
- `test_block_private_ip_172_16_0_0_12` - PASS: Blocks 172.16.0.0/12 range
- `test_block_private_ip_192_168_0_0_16` - PASS: Blocks 192.168.0.0/16 range
- `test_block_localhost_127_0_0_1` - PASS: Blocks loopback addresses
- `test_block_cloud_metadata_endpoint` - PASS: Blocks metadata endpoint
- `test_allow_valid_external_url` - PASS: Allows public IPs
- `test_validate_url_prevents_file_scheme` - PASS: Blocks file:// URLs
- `test_validate_url_prevents_gopher_scheme` - PASS: Blocks gopher:// URLs
- `test_validate_url_allows_http_https` - PASS: Allows http/https URLs

**Implementation Status:**
The `is_private_ip()` and `validate_url()` functions are already implemented in `services/company_enrichment.py`.

### 4. Request Body Size Limit Tests (5 tests)
Tests that oversized request payloads are rejected.

**Status:** 2 passing, 3 skipped

**Size Limits:**
- Job description text (jd_text): max 50,000 characters
- Job description URL (jd_url): max 2,000 characters

**Tests:**
- `test_jd_text_over_50000_chars_rejected_with_422` - PASS: Rejects oversized JD text
- `test_jd_text_at_50000_chars_accepted` - SKIP: Boundary test (needs full request setup)
- `test_jd_url_over_2000_chars_rejected` - PASS: Rejects oversized URLs
- `test_jd_url_at_2000_chars_accepted` - SKIP: Boundary test (needs full request setup)
- `test_multiple_field_size_limits` - SKIP: Needs field enumeration

**Implementation Status:**
Size limits are enforced via Pydantic schema validation in `schemas/job.py`.

### 5. Error Sanitization Tests (5 tests)
Tests that error responses don't expose sensitive information.

**Status:** All passing

**Requirements:**
- No Python stack traces in error responses
- No internal file paths (/Users/..., /home/, C:\, etc.)
- No implementation details exposed
- All errors serializable as JSON

**Tests:**
- `test_500_error_no_stack_trace` - PASS: No Python tracebacks
- `test_error_response_no_internal_file_paths` - PASS: No filesystem paths
- `test_validation_error_sanitized` - PASS: Generic validation errors
- `test_404_error_generic_message` - PASS: Generic 404 message
- `test_error_response_json_serializable` - PASS: JSON serialization works

**Implementation Status:**
Error sanitization is handled by the custom exception handler in `main.py` via `_sanitize_validation_errors()`.

### 6. Security Headers Tests (4 tests)
Tests that required security headers are present in responses.

**Status:** 1 passing, 3 skipped (implementation pending)

**Required Headers:**
- `Content-Security-Policy` (or `X-Content-Security-Policy`)
- `X-Frame-Options: DENY` (or SAMEORIGIN)
- `X-Content-Type-Options: nosniff`

**Tests:**
- `test_csp_header_present` - SKIP: CSP middleware not yet implemented
- `test_x_frame_options_deny` - SKIP: X-Frame-Options middleware not yet implemented
- `test_x_content_type_options_nosniff` - SKIP: X-Content-Type-Options middleware not yet implemented
- `test_security_headers_on_all_endpoints` - SKIP: Comprehensive header check

**Implementation Needed:**
Create middleware to add security headers to all responses.

```python
# Example middleware in main.py
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response
```

### 7. Health Check Tests (8 tests)
Tests that health check endpoints return proper status and dependency information.

**Status:** 4 passing, 4 skipped

**Current Implementation:**
- `GET /health` - Returns version and status (200 OK)

**Tests Passing:**
- `test_health_endpoint_returns_200` - PASS: Endpoint returns 200
- `test_health_endpoint_returns_json` - PASS: Response is valid JSON
- `test_health_endpoint_returns_version_info` - PASS: Contains version field
- `test_health_endpoint_returns_status_healthy` - PASS: Shows healthy status

**Tests Skipped (future implementation):**
- `test_health_endpoint_dependency_status` - Needs detailed dependency info
- `test_health_liveness_endpoint_returns_200` - Needs /health/liveness endpoint
- `test_health_readiness_endpoint_checks_dependencies` - Needs /health/readiness endpoint
- `test_health_readiness_returns_dependency_info` - Needs dependency status detail

**Implementation Roadmap:**
1. Enhance `/health` to include dependency status
2. Add `/health/liveness` for Kubernetes liveness probes
3. Add `/health/readiness` for Kubernetes readiness probes with dependency checks:
   - Database connectivity
   - Vector store (Qdrant) connectivity
   - LLM API availability

### 8. Additional Security Edge Cases (6 tests)
Tests for common attack vectors and edge cases.

**Status:** All passing

**Tests:**
- `test_sql_injection_prevention` - PASS: SQL injection attempts rejected
- `test_xss_prevention_in_responses` - PASS: XSS payloads escaped
- `test_path_traversal_prevention` - PASS: Path traversal blocked
- `test_no_debug_mode_in_production` - PASS: Debug mode disabled
- `test_response_headers_no_server_version` - PASS: Version not exposed
- `test_accept_only_json_or_form` - PASS: Content-type validation

### 9. Integration Tests (5 tests)
Tests combining multiple security features.

**Status:** 4 passing, 1 skipped

**Tests:**
- `test_rate_limited_endpoint_with_cors_headers` - SKIP: Needs rate limiting implementation
- `test_oversized_request_with_valid_cors` - PASS: Size limit enforced with CORS
- `test_invalid_url_with_size_limit` - PASS: SSRF + size limit combined
- `test_health_check_available_during_load` - PASS: Health check accessible
- `test_malformed_request_sanitized_error` - PASS: Errors sanitized properly

### 10. Configuration Tests (3 tests)
Tests for security configuration setup.

**Status:** All skipped (configuration validation needed)

**Tests:**
- `test_cors_config_excludes_wildcard_origin` - SKIP: Configuration validation
- `test_allowed_origins_complete_list` - SKIP: Configuration validation
- `test_environment_variables_not_in_code` - SKIP: Code inspection needed

## Running the Tests

### Run All Security Tests
```bash
cd /Users/benjaminblack/projects/etps/backend
python -m pytest tests/test_security.py -v
```

### Run Specific Test Class
```bash
python -m pytest tests/test_security.py::TestCORSConfiguration -v
```

### Run with Coverage
```bash
python -m pytest tests/test_security.py --cov=services --cov-report=html
```

### Show Test Collection (without running)
```bash
python -m pytest tests/test_security.py -v --collect-only
```

## Test Results Summary

```
36 passed, 19 skipped, 2 warnings in 0.57s
```

### Passing Tests by Category
- SSRF Prevention: 9/9 (100%)
- Error Sanitization: 5/5 (100%)
- Request Body Limits: 2/5 (40%, 3 skipped)
- CORS Configuration: 5/6 (83%, 1 needs implementation)
- Health Check: 4/8 (50%, 4 skipped for future features)
- Security Edge Cases: 6/6 (100%)
- Integration Tests: 4/5 (80%, 1 skipped)

### Skipped Tests by Category
- Rate Limiting: 4/4 (pending implementation)
- Security Headers: 4/4 (pending middleware implementation)
- Health Endpoints: 4/8 (future Kubernetes support)
- Configuration: 3/3 (code inspection needed)

## Sprint 13 Implementation Checklist

Based on the test suite, here's the implementation roadmap:

### Critical (must do for security)
- [ ] Add production origin to CORS configuration
- [ ] Implement security headers middleware (CSP, X-Frame-Options, X-Content-Type-Options)
- [ ] Add rate limiting middleware (10 req/min generation, 60 req/min read)

### Important (should do)
- [ ] Add /health/liveness endpoint
- [ ] Add /health/readiness endpoint with dependency checks
- [ ] Document security configuration in README

### Nice-to-have (can defer)
- [ ] Add Kubernetes probe configuration examples
- [ ] Add detailed dependency status to /health

## References

- **Sprint 13 Requirements:** `/Users/benjaminblack/projects/etps/docs/IMPLEMENTATION_PLAN.md`
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/
- **Rate Limiting:** `slowapi` library (recommended)
- **Security Headers:** https://securityheaders.com/

## Test Maintenance

### Adding New Tests
1. Create test method in appropriate class
2. Use descriptive name: `test_<feature>_<scenario>`
3. Include docstring explaining the test
4. Mark with `@pytest.mark.skip("reason")` if not ready
5. Use proper assertions with clear error messages

### Fixing Skipped Tests
When implementation is complete:
1. Remove `pytest.skip()` calls
2. Update assertions if behavior changed
3. Run full test suite: `pytest tests/test_security.py -v`
4. Update this README with new passing count

## Security Best Practices Covered

1. **Input Validation:** Size limits, type checking, scheme validation
2. **SSRF Prevention:** IP range blocking, private IP detection, metadata endpoint blocking
3. **CORS:** Origin whitelisting, method validation
4. **Error Handling:** Stack trace suppression, sensitive data removal
5. **HTTP Security:** Security headers, content-type enforcement
6. **Health Checks:** Service monitoring, dependency validation
7. **Attack Prevention:** SQL injection, XSS, path traversal protection

## Future Enhancements

- [ ] Add request rate limiting with Redis backend (for distributed deployments)
- [ ] Add IP address whitelisting for admin endpoints
- [ ] Add Web Application Firewall (WAF) rules
- [ ] Add CSRF protection middleware
- [ ] Add request signing/verification for critical operations
- [ ] Add audit logging for security events
- [ ] Add DDoS protection (if needed for public deployment)
- [ ] Add certificate pinning for external API calls

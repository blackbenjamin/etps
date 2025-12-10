---
name: security-review
description: Audit code for OWASP Top 10 vulnerabilities including SQL injection, input validation, authentication, XSS, command injection, and exception handling. Use when reviewing security, checking for vulnerabilities, or before commits.
---

# Security Review for ETPS

## Pre-Commit Security Checklist

### 1. Injection Prevention
- [ ] Use SQLAlchemy ORM (parameterized queries)
- [ ] Validate all inputs with Pydantic schemas
- [ ] Never use raw SQL or string concatenation

```python
# GOOD - ORM
user = db.query(User).filter(User.id == user_id).first()

# BAD - raw SQL (NEVER do this)
db.execute(f"SELECT * FROM users WHERE id={user_id}")
```

### 2. Input Validation
- [ ] Bounds check all parameters (page size, limits)
- [ ] Validate string lengths with Field(max_length=...)
- [ ] Whitelist enum values
- [ ] Request body size limits in schemas

```python
class MyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    count: int = Field(..., gt=0, le=100)
```

### 3. Authentication/Authorization
- [ ] No hardcoded secrets in code
- [ ] Use environment variables for API keys
- [ ] Check user permissions before operations
- [ ] Validate user_id ownership

### 4. Exception Handling
- [ ] No bare `except:` statements
- [ ] Use specific exception types
- [ ] Don't expose stack traces to users
- [ ] Log errors with context

```python
# BAD
try:
    something()
except:
    pass

# GOOD
try:
    something()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise HTTPException(status_code=400, detail="Invalid input")
```

### 5. Regex DoS Prevention
- [ ] Pre-compile regex patterns
- [ ] Limit input length before regex
- [ ] Test with large/malicious inputs

### 6. Data Protection
- [ ] No PII in logs
- [ ] HTTPS in production
- [ ] Sanitize error messages

## Rate Limiting (Active)
- Generation endpoints: 10 requests/minute
- Read endpoints: 60 requests/minute

## Security Commands
```bash
cd backend
bandit -r . -ll --exclude ./tests  # Security scan
python -m pytest tests/test_security.py -v  # Security tests
```

## Best Practices
1. Review code before every commit
2. Use the reviewer agent for security checks
3. Keep dependencies updated
4. Document security decisions

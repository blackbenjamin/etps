# ETPS - Claude Code Project Configuration

## Project Overview

**ETPS (Enterprise Talent Positioning System)** is an AI-powered resume and cover letter tailoring system that optimizes job application materials for specific positions.

**Tech Stack:**
- Backend: Python 3.13, FastAPI, SQLAlchemy, Pydantic
- Frontend: Next.js (planned)
- Database: SQLite (dev), PostgreSQL (prod)
- Vector Store: Qdrant (semantic search)
- LLMs: Claude (primary), GPT-4o (fallback), text-embedding-3-small (embeddings)

## Key Documentation

- `ETPS_PRD.md` - Product Requirements Document (source of truth)
- `docs/IMPLEMENTATION_PLAN.md` - Sprint roadmap and progress
- `docs/ARCHITECTURE.md` - System architecture and service map
- `docs/DATA_MODEL.md` - Database schema reference (v1.3.0)
- `docs/cover_letter_style_guide.md` - Writing style rules
- `backend/README.md` - Backend setup and API reference

## Development Workflow

### Before Every Commit

1. **Run all tests:**
   ```bash
   cd backend && python -m pytest -v --tb=short
   ```

2. **Security review:** Use the reviewer agent to check for vulnerabilities
   - SQL injection, XSS, command injection
   - Input validation and bounds checking
   - Exception handling (no silent failures)
   - ReDoS in regex patterns

3. **Update documentation** if sprint completed

4. **Update data model docs** if `backend/db/models.py` changed
   - Update `docs/DATA_MODEL.md` with new fields/entities
   - Update JSON schema examples if applicable
   - Increment version number

### Commit Convention

| Type | Format | Example |
|------|--------|---------|
| Sprint complete | `feat(sprint-N): <summary>` | `feat(sprint-8c): Implement pagination` |
| Bug fix | `fix: <summary>` | `fix: Resolve null pointer in critic` |
| Docs | `docs: <summary>` | `docs: Update API reference` |

### Sprint Implementation Pattern

1. Read the sprint tasks from `docs/IMPLEMENTATION_PLAN.md`
2. Create todo list with all tasks
3. Implement each task, marking complete as you go
4. Write/update tests (target: all tests pass)
5. Run security review
6. Commit with proper message

## Code Patterns

### Service Structure
All services in `backend/services/` follow this pattern:
- Config loaded from `backend/config/config.yaml`
- Async functions for LLM calls
- Pydantic schemas in `backend/schemas/`
- Database models in `backend/db/models.py`

### Testing Pattern
- Tests in `backend/tests/test_*.py`
- Use `pytest` with `pytest-asyncio`
- Mock LLM with `services/llm/mock_llm.py`
- Mock vector store with `MockVectorStore`

### Key Services

| Service | Purpose |
|---------|---------|
| `resume_tailor.py` | Main orchestrator for resume generation |
| `cover_letter.py` | Cover letter generation with critic loop |
| `critic.py` | Quality evaluation (ATS, style, truthfulness) |
| `skill_gap.py` | Semantic skill matching and gap analysis |
| `pagination.py` | Line budget and page layout simulation |
| `bullet_rewriter.py` | LLM-powered bullet optimization |
| `summary_rewrite.py` | Professional summary generation |

## Security Requirements

### OWASP Top 10 Considerations
- **Injection:** Use parameterized queries, validate all inputs
- **Authentication:** JWT tokens (Sprint 18)
- **Data Exposure:** No secrets in code, use env vars
- **Input Validation:** Bounds check all parameters

### Code Review Checklist
- [ ] No hardcoded secrets or API keys
- [ ] Input validation on all user-facing parameters
- [ ] Specific exception handling (not bare `except:`)
- [ ] Regex patterns pre-compiled and length-limited
- [ ] Database queries use ORM (no raw SQL)

## Current Status

**Completed Sprints:** 1-10C (Core quality, semantic search, learning, pagination, frontend MVP, JD parsing)
**Next:** Sprint 11-14 (Company Intelligence)
**Test Count:** 550 passing

## Useful Commands

```bash
# Run tests
cd backend && python -m pytest -v

# Run specific test file
python -m pytest tests/test_pagination_allocation.py -v

# Check for issues
python -m pytest --tb=long  # Full tracebacks

# Start dev server (future)
uvicorn main:app --reload
```

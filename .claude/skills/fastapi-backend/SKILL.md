---
name: fastapi-backend
description: Develop FastAPI services with SQLAlchemy models, Pydantic schemas, async handlers, and proper error handling. Use when building API endpoints, creating routers, implementing database models, or working with backend/services/ files.
---

# FastAPI Backend Development

## ETPS Architecture
- FastAPI with async/await patterns
- SQLAlchemy ORM for database models (backend/db/models.py)
- Pydantic schemas (backend/schemas/)
- Service layer pattern (backend/services/)
- Config loaded from backend/config/config.yaml

## Key Files
- `backend/main.py` - Application entry point
- `backend/routers/` - API endpoint definitions
- `backend/services/` - Business logic
- `backend/schemas/` - Pydantic request/response models
- `backend/db/models.py` - SQLAlchemy ORM models

## Service Structure Pattern
```python
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from db.database import get_db

router = APIRouter()

@router.post("/endpoint", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def my_endpoint(
    request: Request,  # Must be named 'request' for rate limiter
    body: RequestSchema,
    db: Session = Depends(get_db)
):
    # Implementation
    return result
```

## Key Services
| Service | Purpose |
|---------|---------|
| `resume_tailor.py` | Resume generation orchestrator |
| `cover_letter.py` | Cover letter with critic loop |
| `critic.py` | Quality evaluation (ATS, style) |
| `skill_gap.py` | Semantic skill matching |
| `job_parser.py` | Job description parsing |
| `llm/` | LLM abstraction layer |

## Best Practices
1. Use async/await for all I/O operations
2. Validate input with Pydantic schemas with Field constraints
3. Use specific HTTPException status codes
4. Load config from config.yaml (not hardcoded)
5. Rate limiter requires parameter named exactly `request`
6. Use `body` for request body schemas (not `request`)

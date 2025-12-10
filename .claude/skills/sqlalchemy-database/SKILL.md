---
name: sqlalchemy-database
description: Work with SQLAlchemy ORM, define models, implement relationships, and manage database schema. Use when modifying backend/db/models.py, creating schemas, or working with database entities.
---

# SQLAlchemy Database Models

## ETPS Data Model
- Reference: `docs/DATA_MODEL.md` (current version)
- Dev: SQLite (default)
- Prod: PostgreSQL (Railway)

## Key Models
```
User
├── id, email, name, candidate_profile (JSON)
└── Experiences[]
    ├── employer_name, job_title, dates
    ├── Engagements[] (consulting roles)
    │   └── Bullets[]
    └── Bullets[] (direct roles)

JobProfile
├── id, user_id, job_title, company_name
├── extracted_skills[], must_have[], nice_to_have[]
├── selected_skills[], key_skills[]
└── capability_clusters[]

CompanyProfile
├── id, name, website, industry
├── culture_signals[], data_ai_maturity
└── embedding (384-dim vector)
```

## Model Pattern
```python
from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from db.base import Base

class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("parent_table.id"))
    data = Column(JSON, default=dict)

    # Relationships
    parent = relationship("ParentModel", back_populates="children")
```

## PostgreSQL Notes
- B-tree indexes cannot be on JSON columns (use GIN if needed)
- Railway's `postgres://` URL auto-converts to `postgresql://`
- DATABASE_URL env var configures connection

## After Changing Models
1. Update `docs/DATA_MODEL.md` with new fields
2. Update JSON schema examples
3. Increment version number
4. Test with both SQLite and PostgreSQL

## Best Practices
1. Always use ORM, never raw SQL
2. Use relationships for foreign keys
3. Add indexes on frequently queried columns
4. Document changes in DATA_MODEL.md
5. Use parameterized queries (ORM handles this)

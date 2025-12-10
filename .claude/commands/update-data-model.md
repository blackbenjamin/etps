# Update Data Model Documentation

Run this command after making changes to database models to keep documentation in sync.

## When to Use
- After adding/modifying fields in `backend/db/models.py`
- After adding new model classes
- After changing JSON field schemas
- After adding/removing indexes or relationships

## Workflow

### 1. Identify Changes
Check what was modified:
```bash
git diff backend/db/models.py
```

### 2. Update DATA_MODEL.md
Open `/Users/benjaminblack/projects/etps/docs/DATA_MODEL.md` and update:

**For new fields:**
- Add row to the entity's field table
- Include: Field name, Type, Constraints, Description
- If JSON field, add schema example

**For new entities:**
- Add to ERD diagram
- Create new field table section
- Document relationships
- Add any new indexes

**For schema changes:**
- Update JSON schema examples
- Update Pydantic schema references

### 3. Update Version
Increment version in DATA_MODEL.md header:
- Patch (1.3.1): Field additions, minor changes
- Minor (1.4.0): New entities, significant changes
- Major (2.0.0): Breaking changes

### 4. Update Related Docs
Check if changes affect:
- `docs/ARCHITECTURE.md` (service descriptions)
- `CLAUDE.md` (if new patterns introduced)
- Pydantic schemas in `backend/schemas/`

### 5. Verify Consistency
- Ensure model docstrings match DATA_MODEL.md
- Ensure JSON schemas match Pydantic models
- Run tests to verify nothing broke

## Checklist
- [ ] Field table updated for all changed entities
- [ ] ERD updated if relationships changed
- [ ] JSON schemas documented for new/changed JSON fields
- [ ] Indexes documented
- [ ] Version number incremented
- [ ] Migration notes added if applicable

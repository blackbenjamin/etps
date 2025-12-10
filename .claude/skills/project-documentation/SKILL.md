---
name: project-documentation
description: Update and maintain project documentation including CLAUDE.md, API docs, architecture docs, and data model specs. Use when updating docs, documenting features, or after completing sprints.
---

# ETPS Documentation Management

## Key Documents
| Document | Purpose | Update When |
|----------|---------|-------------|
| `CLAUDE.md` | Project config for Claude Code | Workflows change |
| `ETPS_PRD.md` | Product Requirements (source of truth) | Requirements change |
| `docs/IMPLEMENTATION_PLAN.md` | Sprint roadmap | Sprint completes |
| `docs/ARCHITECTURE.md` | System architecture | Services added |
| `docs/DATA_MODEL.md` | Database schema | Models change |
| `docs/cover_letter_style_guide.md` | AI writing rules | Style rules change |

## Update Triggers

### After Completing a Sprint
Update `docs/IMPLEMENTATION_PLAN.md`:
- Mark completed tasks with [x]
- Update phase status (COMPLETE/IN PROGRESS)
- Update test count
- Note any blockers or changes

### After Changing Database Models
Update `docs/DATA_MODEL.md`:
1. Add new fields with types
2. Update relationships diagram
3. Update JSON schema examples
4. Increment version (e.g., v1.4.2 -> v1.4.3)

### After Adding Services
Update `docs/ARCHITECTURE.md`:
- Add to service map diagram
- Document inputs/outputs
- Add to API endpoints table

## Version Numbering
```
Major.Minor.Patch
  │     │     └── Documentation clarifications
  │     └──────── New fields/entities
  └────────────── Breaking schema changes
```

## Current Status
- **Phase 1A-1C**: COMPLETE (Sprints 1-14)
- **Live URLs**:
  - Frontend: https://etps.benjaminblack.consulting
  - Backend: https://etps-production.up.railway.app
- **Tests**: 700+ passing
- **Next**: Phase 2 (Sprints 15-17) - Company Intelligence

## Documentation Style
- Use backticks for `code` and `file_paths`
- Use code blocks with language tags
- Use tables for structured data
- Keep line length reasonable (~80 chars)
- Link between related documents

## Best Practices
1. Update docs immediately after changes
2. Keep IMPLEMENTATION_PLAN.md current
3. Document all schema changes
4. Include examples in technical docs
5. Commit docs with related code changes

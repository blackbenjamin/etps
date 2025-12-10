# Commit Sprint Command

Complete a sprint with full validation, security review, and proper commit.

## Arguments
- Sprint identifier (e.g., "8c", "9", "10")

## Workflow

### 1. Run All Tests
```bash
cd /Users/benjaminblack/projects/etps/backend
python -m pytest -v --tb=short
```
All tests must pass before proceeding.

### 2. Security Review
Use the `/review-security` command or reviewer agent to check for:
- Input validation issues
- Injection vulnerabilities
- Error handling problems
- Resource management issues

Fix any CRITICAL or HIGH severity issues before committing.

### 3. Update Documentation
- Update `docs/IMPLEMENTATION_PLAN.md`:
  - Mark sprint status as ✅ COMPLETE
  - Update test count
  - Add completion date
- Update `CLAUDE.md` if needed

### 4. Stage and Commit
```bash
git add -A
git status  # Review what's being committed
```

Commit with proper message format:
```
feat(sprint-N): <Brief summary>

<Detailed bullet points of what was implemented>

Security review: Passed
Tests: X passing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 5. Verify
```bash
git log -1  # Check commit message
git show --stat  # Review changes
```

## Pre-Commit Checklist
- [ ] All tests passing
- [ ] Security review completed (no CRITICAL/HIGH issues)
- [ ] Documentation updated
- [ ] No secrets in staged files
- [ ] Commit message follows convention

# Security Review Command

Perform a comprehensive security review of recent code changes before committing.

## Instructions

1. **Identify changed files** - Check `git status` and `git diff` to see what's modified

2. **Review each file for:**

   **Input Validation:**
   - Are all user inputs validated and bounds-checked?
   - Are string lengths limited to prevent DoS?
   - Are numeric parameters checked for valid ranges?

   **Injection Vulnerabilities:**
   - SQL: Using ORM? No raw queries with string formatting?
   - Command: No shell commands with user input?
   - Regex: Patterns pre-compiled? Input length limited?

   **Error Handling:**
   - No bare `except:` clauses?
   - Specific exception types caught?
   - No sensitive data in error messages?
   - Full tracebacks logged for debugging?

   **Data Security:**
   - No hardcoded secrets or API keys?
   - Sensitive data not logged?
   - Proper access controls?

   **Resource Management:**
   - No unbounded loops or recursion?
   - File handles closed properly?
   - Database connections managed?

3. **Report findings by severity:**
   - **CRITICAL**: Must fix before merge (security vulnerabilities)
   - **HIGH**: Should fix before merge (potential exploits)
   - **MEDIUM**: Fix before release (code quality)
   - **LOW**: Nice to have (best practices)

4. **Provide specific fixes** for each issue found

Use the `reviewer` agent with `subagent_type=reviewer` for this task.

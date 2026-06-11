Review the current diff or specified code for correctness bugs and reuse/simplification/efficiency improvements.

Target: $ARGUMENTS (if empty, review the current staged diff or recent changes)

Steps:
1. Read the relevant files or diff
2. Check for: correctness bugs, security issues (XSS, injection, auth), performance problems, code duplication, missing error handling at system boundaries
3. Rate each finding: critical / warning / suggestion
4. Group findings by file and line number
5. Provide a summary verdict: ready to ship / needs fixes / major issues

Format findings as:
- [CRITICAL/WARNING/SUGGESTION] file:line — description + recommended fix

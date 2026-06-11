Complete a security review of the pending changes or specified code.

Scope: $ARGUMENTS (if empty, review the current branch diff vs main)

Check for:
1. Injection vulnerabilities (SQL, command, XSS, template)
2. Authentication and authorization flaws
3. Sensitive data exposure (hardcoded secrets, API keys, PII in logs)
4. Insecure dependencies (known CVEs)
5. OWASP Top 10 issues
6. Input validation gaps at system boundaries
7. Insecure direct object references
8. Security misconfigurations

Format:
- [SEVERITY: Critical/High/Medium/Low] Category — file:line — description — remediation
- Final verdict: SAFE / NEEDS FIXES / CRITICAL ISSUES

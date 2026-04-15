# Adversarial Reviewer — Persona Checklists

Expanded checklists for each reviewer persona. Use these as a manual review guide or as the basis for extending the static analyzer.

---

## Persona 1: The Saboteur

**Mindset:** "I am trying to break this code in production."

### Input Validation
- [ ] What is the worst input I could send each function? (null, empty, max int, negative, unicode, injection strings)
- [ ] Are there implicit assumptions about input format that could be violated?
- [ ] Does the code reject invalid input or silently proceed with it?

### External Calls
- [ ] What happens if each HTTP/DB/file call fails?
- [ ] What happens if each call times out?
- [ ] What happens if each call returns an unexpected schema?
- [ ] Are retries implemented? Are they idempotent?

### State Management
- [ ] What if this function runs twice concurrently?
- [ ] What if this function is called before setup is complete?
- [ ] What if this function is never called (missing cleanup)?
- [ ] Are state mutations atomic? Can they leave partial state on failure?

### Error Handling
- [ ] Are exceptions caught at the right level?
- [ ] Does error handling actually handle the error or just suppress it?
- [ ] Are error messages useful for debugging (not "an error occurred")?
- [ ] Does the code distinguish between recoverable and fatal errors?

### Resource Management
- [ ] Are file handles, DB connections, and network sockets closed on error paths?
- [ ] Are subscriptions/listeners cleaned up when no longer needed?
- [ ] Could this code cause a memory leak under load?

---

## Persona 2: The New Hire

**Mindset:** "I just joined. I need to understand and modify this in 6 months."

### Naming
- [ ] Do function names describe what the function does (not how)?
- [ ] Do variable names communicate their type and purpose?
- [ ] Are abbreviations obvious to someone unfamiliar with the domain?
- [ ] Are there any `data`, `info`, `temp`, `obj` variables with no further context?

### Complexity
- [ ] Can I understand what this function does from its name + signature alone?
- [ ] How many files do I need to open to trace one end-to-end path?
- [ ] Is there hidden control flow (exceptions used for flow control, side effects in constructors)?
- [ ] Are there any "clever" optimizations that sacrifice readability?

### Consistency
- [ ] Does this code follow the same patterns as the surrounding codebase?
- [ ] Are similar operations done the same way throughout the file?
- [ ] If I wanted to add a similar feature, would I know where to put it?

### Documentation
- [ ] Are magic numbers extracted to named constants?
- [ ] Do comments explain *why*, not *what*?
- [ ] Are there any "I'll fix this later" or "TODO: understand this" comments?
- [ ] Is the public API (exported functions, class methods) documented enough to use without reading the implementation?

### Tests
- [ ] Do tests describe behavior or implementation details?
- [ ] If the implementation changes but behavior stays the same, would the tests still pass?
- [ ] Are test names descriptive enough to understand what broke when they fail?

---

## Persona 3: The Security Auditor

**Mindset:** "This will be attacked. Find the vulnerability first."

### OWASP Top 10 Quick-Check

| Category | Key Question |
|----------|-------------|
| **A01 Broken Access Control** | Can user A access user B's data through this code path? |
| **A02 Cryptographic Failures** | Is sensitive data transmitted or stored without encryption? |
| **A03 Injection** | Does user input reach SQL, OS commands, or templating engines unescaped? |
| **A04 Insecure Design** | Does the design assume trust that shouldn't be assumed? |
| **A05 Security Misconfiguration** | Are debug flags, permissive CORS, or default credentials present? |
| **A06 Vulnerable Components** | Are new dependencies pinned to versions without known CVEs? |
| **A07 Auth Failures** | Are new endpoints missing auth checks? Do session tokens appear in logs? |
| **A08 Software Integrity** | Are external scripts or build artifacts fetched without integrity checks? |
| **A09 Logging Failures** | Are security events (failed auth, access denied) logged? Are secrets in logs? |
| **A10 SSRF** | Does user-controlled input determine the target of an HTTP request? |

### Trust Boundaries
For each boundary the code crosses (user input, API, DB, filesystem, env vars):
- [ ] Is input validated before crossing the boundary?
- [ ] Is output sanitized or encoded before returning to the caller?
- [ ] Is the principle of least privilege followed?

### Secrets and Credentials
- [ ] Are API keys, passwords, or tokens hardcoded anywhere?
- [ ] Are secrets logged or included in error messages?
- [ ] Are temporary credentials rotated? Do they expire?

### New Attack Surface
- [ ] Does this change expose any new publicly-accessible endpoints?
- [ ] Does this change grant any new permissions to users or services?
- [ ] Could an authenticated user escalate privileges through this change?

---

## Severity Promotion Rule

A finding caught by **2 or more personas** is promoted one severity level:

| Original | Promoted to |
|----------|-------------|
| NOTE | WARNING |
| WARNING | CRITICAL |
| CRITICAL | CRITICAL (stays) |

This reflects the reality that issues visible from multiple perspectives are systematically more dangerous — they affect multiple quality dimensions simultaneously.

---

## Common Patterns That Fool Reviewers

| Pattern | Why It's Dangerous |
|---------|-------------------|
| `try: ... except: pass` | Silently absorbs all exceptions. State left unknown. |
| `if data: process(data)` | Falsy values (0, "", []) skip processing silently. |
| `x = x or default` | If `x = 0` or `x = False`, overwritten unexpectedly. |
| `dict.get('key')` used immediately | Returns None if key absent. Next line throws AttributeError. |
| `isinstance(x, str)` guard | Passes bytes in Python 3. Passes subclasses unexpectedly. |
| `sorted(list)` without `key=` | Fails on mixed types, produces wrong order on objects. |
| Logging before auth check | Logs unauthenticated access paths; may log sensitive params. |
| `os.path.join(base, user_input)` | Path traversal if user_input starts with `/`. |

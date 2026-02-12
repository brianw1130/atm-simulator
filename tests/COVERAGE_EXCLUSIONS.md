# Coverage Exclusions Log

All lines excluded from coverage measurement via `# pragma: no cover` must be
documented here with justification. This file is reviewed at every sprint gate.

## Format

| File | Line(s) | Exclusion Reason | Date Added | Reviewer |
|------|---------|-----------------|------------|----------|
| — | — | No exclusions yet | — | — |

## Valid Exclusion Reasons

1. **Defensive error handling** — Code that guards against conditions that cannot
   be triggered in the test environment (e.g., database connection failures during migration).
2. **Abstract base class methods** — Methods that exist only to define an interface contract.
3. **Platform-specific branches** — Code paths that only execute on specific OS or
   Python versions that are not part of the test matrix.
4. **Framework-internal paths** — Code paths triggered only by framework internals
   that cannot be exercised through the public API.

## Invalid Exclusion Reasons

- "It's hard to test" — Refactor the code to make it testable.
- "It's just boilerplate" — Boilerplate can contain bugs too.
- "It works, I checked manually" — Manual verification is not repeatable.

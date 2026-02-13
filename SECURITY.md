# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.0.x   | Yes       |
| < 2.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly. **Do not open a public GitHub issue.**

Instead, please email **brianw1130@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (optional)

You should receive a response within 48 hours acknowledging receipt.

## Security Measures

This project implements the following security controls:

- **Authentication:** bcrypt PIN hashing with application-level pepper
- **Session management:** Cryptographically random tokens with 2-minute idle timeout
- **Input validation:** Pydantic schemas validate all API inputs before reaching business logic
- **SQL injection prevention:** SQLAlchemy parameterized queries (no raw SQL)
- **Rate limiting:** 5 auth attempts per card per 15-minute window; 3-attempt lockout per session
- **Audit logging:** All authentication attempts, transactions, and admin actions are logged

## CI Security Scanning

Every pull request is scanned by:

| Tool | Category |
|------|----------|
| **CodeQL** | Deep SAST (SQL injection, XSS, taint tracking) for Python and TypeScript |
| **Bandit** | Python-specific SAST (hardcoded secrets, eval, weak crypto) |
| **pip-audit** | Python dependency CVE scanning |
| **npm audit** | Frontend dependency CVE scanning |
| **Trivy** | Filesystem vulnerability + Terraform IaC misconfiguration scanning |
| **Gitleaks** | Secret detection across full git history |
| **Dependabot** | Automated PRs for vulnerable dependencies (pip, npm, GitHub Actions) |

## Disclaimer

This is an **educational simulator** and should not be used as a production banking system. While security best practices are followed, this application has not undergone a formal third-party security audit.

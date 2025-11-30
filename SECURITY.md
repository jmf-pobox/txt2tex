# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in txt2tex, please report it responsibly:

1. **Do NOT open a public GitHub issue** for security vulnerabilities
2. Email the maintainer directly at the email address listed in the GitHub profile
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

## Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Resolution target**: Within 30 days for critical issues

## Scope

This security policy covers:
- The txt2tex Python package
- Generated LaTeX output
- CLI tool behavior

Out of scope:
- Third-party dependencies (report to their maintainers)
- The fuzz typechecker (separate project)

## Security Best Practices

When using txt2tex:
- Only process trusted input files
- Review generated LaTeX before compilation in sensitive environments
- Keep dependencies updated (`hatch run pip list --outdated`)


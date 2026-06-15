# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately.

**Do not open a public issue.**

Preferred methods:
- Email the maintainer (via GitHub profile or security advisory).
- Use GitHub's private vulnerability reporting (if enabled for the repo): https://github.com/MinG-98/fakeloc/security/advisories/new

Please include:
- Description of the vulnerability and impact
- Steps to reproduce
- Any potential fixes or mitigations you have identified

We will acknowledge receipt within 48 hours and aim to release a fix or mitigation as soon as possible.

## Scope

This project involves:
- Local sudo password handling (via askpass helper and temp files)
- USB communication with iPhone via pymobiledevice3
- Simulated GPS data sent to the device

We are particularly interested in reports related to:
- Local privilege escalation via the password handling
- Exposure of user data or state files
- Issues in dependency usage that could lead to remote code execution or data leaks

Thank you for helping keep the project and its users secure.

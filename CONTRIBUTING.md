# Contributing to fakeloc

Thank you for your interest in contributing to fakeloc!

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

- Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) when opening an issue.
- Include as much detail as possible: macOS version, Python version, iPhone model, exact commands, and error output.
- Check existing issues first to avoid duplicates.

### Suggesting Features

- Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).
- Describe the use case and why it would benefit users.

### Pull Requests

1. Fork the repository and create your branch from `main`.
2. Make your changes (remember: do not modify core implementation files unless necessary for your contribution).
3. Ensure the code style is consistent (we use standard Python formatting).
4. Test your changes locally if possible (`fakeloc --help`, GUI on macOS).
5. Update documentation (README, etc.) if your change affects usage.
6. Open a Pull Request with a clear title and description.
7. Link any related issues.

We will review PRs as soon as possible. Please be patient.

## Development Setup

```bash
git clone https://github.com/MinG-98/fakeloc.git
cd fakeloc
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[gui]"  # GUI deps are macOS only
```

See the README for full usage and requirements (macOS + Developer Mode on iPhone required for full testing).

## Commit Messages

We prefer clear, conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `chore:` for maintenance, tooling, etc.

## Questions?

Open a discussion or issue. We're happy to help!

Thank you for helping make fakeloc better!

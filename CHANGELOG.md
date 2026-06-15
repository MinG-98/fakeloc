# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-15

### Added
- Initial release of fakeloc: iPhone GPS spoofing tool over USB using pymobiledevice3.
- CLI (`fakeloc`) for terminal-based location spoofing with presets and custom coordinates.
- GUI (`fakeloc-gui`) native macOS floating window (requires optional dependencies).
- Built-in presets for major cities worldwide (US, Asia, Europe, etc.).
- Keep-alive mechanism: resends coordinates every second to maintain spoofed location.
- Support for starting RSD tunnel via USB (with sudo/askpass helpers).
- Environment variable configuration for all paths and helpers.
- Bilingual documentation (中文 + English).

### Changed
- Professional project packaging with setuptools and pyproject.toml.
- Restructured source layout under `src/fakeloc/`.
- Separate English and Chinese README files.

[0.1.0]: https://github.com/MinG-98/fakeloc/releases/tag/v0.1.0

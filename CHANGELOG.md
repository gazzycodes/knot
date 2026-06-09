# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-09

### Added
- Static import analyzer that maps a project's modules and resolves absolute
  and relative `import` / `from ... import` statements to internal modules.
- Iterative Tarjan strongly-connected-components implementation and cycle
  detection with a concrete example path for each cycle.
- CLI (`knot`) with `text`, `json`, and `mermaid` output formats and a
  CI-friendly non-zero exit code when cycles are found (`--no-fail` to override).
- Test suite covering discovery, resolution, cycle detection, and the CLI.

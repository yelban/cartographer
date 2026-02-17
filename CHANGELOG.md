# Changelog

All notable changes to Cartographer are documented in this file.

## [2.0.0] - 2026-02-17

### Added

- **Scanner**: `pathspec` library for full gitignore-compatible pattern matching (replaces hand-written parser)
- **Scanner**: `!pattern` negation support — e.g. `dist/*` + `!dist/config.json`
- **Scanner**: Nested `.gitignore` support at each directory level
- **Scanner**: Symlink loop prevention via resolved path tracking
- **Scanner**: New text extensions: `.astro`, `.cjs`, `.mjs`, `.bicep`
- **Scanner**: New text filenames: `go.mod`, `go.sum`, `.dockerignore`
- **Scanner**: New default ignores: `.turbo/`, `.nx/`, `.svelte-kit/`
- **Workflow**: Structured subagent output schema with `COMPLETE/PARTIAL/FAILED` status
- **Workflow**: `[EXTERNAL/UNKNOWN]` labeling for unresolvable imports
- **Workflow**: Graceful degradation for partial subagent failures
- **Workflow**: SHA-256 hash-based change detection fallback for non-git environments
- **Workflow**: Verbatim preservation rule for incremental updates
- **Map**: Entry Points section in `CODEBASE_MAP.md` template
- **Map**: Data Models & Schema section
- **Map**: External Integrations section

### Changed

- **Scanner**: Token fallback heuristic from `len(text) // 4` to `len(text) // 3` (safer for code)
- **Scanner**: `pathspec` added as PEP 723 inline dependency alongside `tiktoken`
- **Workflow**: Subagent per-file analysis capped at 150 words

### Removed

- **Scanner**: `parse_gitignore()`, `matches_pattern()`, `should_ignore()` (replaced by pathspec)

## [1.4.0] - 2026-01-15

### Added

- **Scanner**: UV inline script dependencies (PEP 723) — `uv run scan-codebase.py` auto-installs tiktoken

### Fixed

- **Workflow**: Timestamp generation now uses actual system time (`date -u`) instead of hardcoded values

## [1.3.0] - 2026-01-15

### Added

- **Workflow**: Star prompt on completion linking to GitHub repo

## [1.2.0] - 2026-01-14

### Changed

- **Workflow**: Token budgets adjusted from 500k to 150k per subagent to match standard Sonnet 200k context window

### Added

- **README**: Token usage warning about subagent costs

## [1.1.0] - 2026-01-13

### Added

- **Workflow**: Mermaid diagram support in `CODEBASE_MAP.md` (architecture + sequence diagrams)

### Changed

- **Workflow**: Efficiency improvements to subagent orchestration

## [1.0.0] - 2026-01-13

### Added

- Initial release of Cartographer codebase mapping skill
- Orchestrator-Worker pattern: Opus plans, Sonnet subagents read and analyze
- `scan-codebase.py` recursive scanner with tiktoken token counting
- `.gitignore` basic pattern matching (no negation)
- Binary file detection via null-byte sniffing + extension whitelist
- `CODEBASE_MAP.md` output with System Overview, Module Guide, Data Flow, Conventions, Gotchas, Navigation Guide
- `CLAUDE.md` auto-update with codebase summary
- Marketplace plugin structure for `claude plugins install`

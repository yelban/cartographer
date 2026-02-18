# Cartographer

A Claude Code plugin that maps and documents codebases of any size using parallel AI subagents.

## What it does

Cartographer orchestrates multiple Sonnet subagents (with 1M token context windows) to analyze your entire codebase in parallel, then synthesizes their findings into comprehensive documentation:

- `docs/CODEBASE_MAP.md` - Detailed architecture map with file purposes, dependencies, data flows, and navigation guides
- Updates `CLAUDE.md` with a summary pointing to the map

## Installation

### Via Claude Code Plugins Registry

```bash
claude plugins install cartographer
```

### Manual Installation

Clone to your Claude skills directory:

```bash
git clone https://github.com/yelban/cartographer.git ~/.claude/skills/cartographer
```

Or for project-specific use:

```bash
git clone https://github.com/yelban/cartographer.git .claude/skills/cartographer
```

### Dependencies

The scanner script requires tiktoken and pathspec (auto-installed via UV):

```bash
# Recommended: dependencies install automatically with uv run
uv run scan-codebase.py .

# Manual install if not using UV:
pip install tiktoken pathspec
```

## Usage

Simply invoke the skill:

```
/cartographer
```

Or say:
- "map this codebase"
- "create codebase map"
- "document the architecture"
- "understand this codebase"

### Update Mode

If `docs/CODEBASE_MAP.md` already exists, Cartographer will:

1. Check git history for changes since last mapping
2. Only re-analyze changed modules
3. Merge updates with existing documentation

Just run `/cartographer` again to update.

## How it Works

```
/cartographer invoked
        |
        v
+---------------------------------------+
|  1. Run scripts/scan-codebase.py      |
|     - Recursive file tree             |
|     - Token count per file            |
|     - Respects .gitignore             |
+---------------------------------------+
        |
        v
+---------------------------------------+
|  2. Plan subagent assignments         |
|     - Group files by module           |
|     - Balance token budgets           |
|     - Target ~150k tokens per agent   |
+---------------------------------------+
        |
        v
+---------------------------------------+
|  3. Spawn Sonnet subagents PARALLEL   |
|     - Each reads assigned files       |
|     - Analyzes purpose, dependencies  |
|     - Returns structured summary      |
+---------------------------------------+
        |
        v
+---------------------------------------+
|  4. Synthesize all reports            |
|     - Merge subagent outputs          |
|     - Build architecture diagram      |
|     - Create navigation guides        |
+---------------------------------------+
        |
        v
+---------------------------------------+
|  5. Write docs/CODEBASE_MAP.md        |
|     Update CLAUDE.md with summary     |
+---------------------------------------+
```

## Output Structure

The generated `docs/CODEBASE_MAP.md` includes:

- **System Overview** - Mermaid architecture diagram
- **Directory Structure** - Annotated file tree
- **Module Guide** - Per-module documentation with:
  - Purpose and entry points
  - Key files with token counts
  - Exports and dependencies
- **Entry Points** - Where the application starts (v2.0)
- **Data Models & Schema** - Core data structures and ORM entities (v2.0)
- **External Integrations** - Third-party APIs and services (v2.0)
- **Data Flow** - Request flows, auth flows, etc.
- **Conventions** - Naming, patterns, style
- **Gotchas** - Non-obvious behaviors and warnings
- **Navigation Guide** - How to add features, modify systems

## Token Budgets

| Model | Context Window | Budget per Subagent |
|-------|---------------|---------------------|
| Sonnet | 200,000 | 150,000 |
| Opus | 200,000 | 100,000 |
| Haiku | 200,000 | 100,000 |

Cartographer uses Sonnet subagents by default for best balance of capability and cost.

## Configuration

The scanner uses `pathspec` for full gitignore-compatible pattern matching:
- **`--exclude PATTERN`** flag to exclude specific paths (gitignore format, repeatable) (v2.1)
- **Negation patterns** (`!pattern`) fully supported (v2.0)
- **Nested `.gitignore`** files respected at each directory level (v2.0)
- Sensible defaults for ignoring `node_modules`, `dist`, `build`, `.turbo`, `.nx`, etc.
- Skipping binary files (null-byte sniffing + extension whitelist)
- Skipping files over 1MB or 50k tokens
- Symlink loop detection prevents infinite recursion (v2.0)
- Tool outputs (`CODEBASE_MAP.md`, `SPEC.md`, etc.) excluded by default to prevent recursive self-reference (v2.1)

## License

MIT

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["tiktoken", "pathspec"]
# ///
"""
Codebase Scanner for Cartographer v2.0
Scans a directory tree, respects .gitignore (with negation and nested support),
and outputs file paths with token counts.
Uses tiktoken for accurate Claude-compatible token estimation.
Uses pathspec for full gitignore-compatible pattern matching.

Run with: uv run scan-codebase.py [path]
UV will automatically install dependencies in an isolated environment.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import tiktoken
except ImportError:
    print("ERROR: tiktoken not installed.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Recommended: Install UV for automatic dependency handling:", file=sys.stderr)
    print("  curl -LsSf https://astral.sh/uv/install.sh | sh", file=sys.stderr)
    print("  Then run: uv run scan-codebase.py", file=sys.stderr)
    print("", file=sys.stderr)
    print("Or install dependencies manually: pip install tiktoken pathspec", file=sys.stderr)
    sys.exit(1)

try:
    import pathspec
except ImportError:
    print("ERROR: pathspec not installed.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Recommended: Use UV which auto-installs dependencies:", file=sys.stderr)
    print("  uv run scan-codebase.py", file=sys.stderr)
    print("", file=sys.stderr)
    print("Or install manually: pip install pathspec", file=sys.stderr)
    sys.exit(1)


# Default ignore patterns (gitignore format, evaluated before .gitignore)
DEFAULT_IGNORE_PATTERNS = [
    # Directories (trailing / = directory-only)
    ".git/",
    ".svn/",
    ".hg/",
    "node_modules/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "venv/",
    ".venv/",
    "env/",
    "dist/",
    "build/",
    ".next/",
    ".nuxt/",
    ".output/",
    "coverage/",
    ".coverage/",
    ".nyc_output/",
    "target/",
    "vendor/",
    ".bundle/",
    ".cargo/",
    ".turbo/",
    ".nx/",
    ".svelte-kit/",
    # Files and directories (no trailing / = match both)
    ".env",
    ".DS_Store",
    "Thumbs.db",
    # File patterns
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.o",
    "*.a",
    "*.lib",
    "*.class",
    "*.jar",
    "*.war",
    "*.egg",
    "*.whl",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "Cargo.lock",
    "poetry.lock",
    "Gemfile.lock",
    "composer.lock",
    # Binary/media
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.svg",
    "*.webp",
    "*.mp3",
    "*.mp4",
    "*.wav",
    "*.avi",
    "*.mov",
    "*.pdf",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.rar",
    "*.7z",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.eot",
    "*.otf",
    # Large generated files
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.chunk.js",
    "*.bundle.js",
]


def load_gitignore(directory: Path) -> list[str]:
    """Load and parse a .gitignore file from a directory."""
    gitignore_path = directory / ".gitignore"
    if not gitignore_path.exists():
        return []
    patterns = []
    with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped)
    return patterns


def count_tokens(text: str, encoding: tiktoken.Encoding) -> int:
    """Count tokens in text using tiktoken."""
    try:
        return len(encoding.encode(text))
    except Exception:
        # Conservative fallback for code (denser tokens than English prose)
        return len(text) // 3


def is_text_file(path: Path) -> bool:
    """Check if a file is likely a text file."""
    # Check by extension first
    text_extensions = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".vue",
        ".svelte",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".xml",
        ".md",
        ".mdx",
        ".txt",
        ".rst",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".ps1",
        ".bat",
        ".cmd",
        ".sql",
        ".graphql",
        ".gql",
        ".proto",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".java",
        ".kt",
        ".kts",
        ".scala",
        ".clj",
        ".cljs",
        ".edn",
        ".ex",
        ".exs",
        ".erl",
        ".hrl",
        ".hs",
        ".lhs",
        ".ml",
        ".mli",
        ".fs",
        ".fsx",
        ".fsi",
        ".cs",
        ".vb",
        ".swift",
        ".m",
        ".mm",
        ".h",
        ".hpp",
        ".c",
        ".cpp",
        ".cc",
        ".cxx",
        ".r",
        ".R",
        ".jl",
        ".lua",
        ".vim",
        ".el",
        ".lisp",
        ".scm",
        ".rkt",
        ".zig",
        ".nim",
        ".d",
        ".dart",
        ".v",
        ".sv",
        ".vhd",
        ".vhdl",
        ".tf",
        ".hcl",
        ".dockerfile",
        ".containerfile",
        ".makefile",
        ".cmake",
        ".gradle",
        ".groovy",
        ".rake",
        ".gemspec",
        ".podspec",
        ".cabal",
        ".nix",
        ".dhall",
        ".jsonc",
        ".json5",
        ".cson",
        ".ini",
        ".cfg",
        ".conf",
        ".config",
        ".env",
        ".env.example",
        ".env.local",
        ".env.development",
        ".env.production",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        ".prettierrc",
        ".eslintrc",
        ".stylelintrc",
        ".babelrc",
        ".nvmrc",
        ".ruby-version",
        ".python-version",
        ".node-version",
        ".tool-versions",
        # v2.0 additions
        ".astro",
        ".cjs",
        ".mjs",
        ".bicep",
    }

    suffix = path.suffix.lower()
    if suffix in text_extensions:
        return True

    # Check for extensionless files that are commonly text
    name = path.name.lower()
    text_names = {
        "readme",
        "license",
        "licence",
        "changelog",
        "authors",
        "contributors",
        "copying",
        "dockerfile",
        "containerfile",
        "makefile",
        "rakefile",
        "gemfile",
        "procfile",
        "brewfile",
        "vagrantfile",
        "justfile",
        "taskfile",
        # v2.0 additions
        "go.mod",
        "go.sum",
        ".dockerignore",
    }
    if name in text_names:
        return True

    # Try to detect binary by reading first bytes
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            # Check for null bytes (binary indicator)
            if b"\x00" in chunk:
                return False
            # Try to decode as UTF-8
            try:
                chunk.decode("utf-8")
                return True
            except UnicodeDecodeError:
                return False
    except Exception:
        return False


def scan_directory(
    root: Path,
    encoding: tiktoken.Encoding,
    max_file_tokens: int = 50000,
    exclude_patterns: list[str] | None = None,
) -> dict:
    """
    Scan a directory and return file information with token counts.

    Uses pathspec for gitignore-compatible pattern matching with full
    negation (!pattern) and nested .gitignore support.

    Returns a dict with:
    - files: list of {path, tokens, size_bytes}
    - directories: list of directory paths
    - total_tokens: sum of all file tokens
    - total_files: count of files
    - skipped: list of skipped files (binary, too large, etc.)
    """
    root = root.resolve()
    visited_real_paths: set[str] = set()

    exclude_spec = None
    if exclude_patterns:
        exclude_spec = pathspec.PathSpec.from_lines("gitwildmatch", exclude_patterns)

    files = []
    directories = []
    skipped = []
    total_tokens = 0

    # Build root ignore spec: defaults + root .gitignore
    root_patterns = list(DEFAULT_IGNORE_PATTERNS) + load_gitignore(root)
    root_spec = pathspec.PathSpec.from_lines("gitwildmatch", root_patterns)

    def is_ignored(
        rel_path: str,
        is_dir: bool,
        specs: list[tuple[str, "pathspec.PathSpec"]],
    ) -> bool:
        """Check if a relative path should be ignored.

        Args:
            rel_path: Path relative to scan root.
            is_dir: Whether this path is a directory.
            specs: List of (base_dir, spec) tuples. base_dir is "." for root.
        """
        for base_dir, spec in specs:
            # Compute path relative to this spec's base directory
            if base_dir == ".":
                local_path = rel_path
            elif rel_path.startswith(base_dir + "/"):
                local_path = rel_path[len(base_dir) + 1 :]
            else:
                continue

            # Check without trailing / (matches file-or-dir patterns)
            if spec.match_file(local_path):
                return True
            # For directories, also check with trailing / (matches dir-only patterns)
            if is_dir and spec.match_file(local_path + "/"):
                return True
        return False

    def walk(
        current: Path,
        specs: list[tuple[str, "pathspec.PathSpec"]],
        depth: int = 0,
    ):
        nonlocal total_tokens

        if current.is_dir():
            # Symlink loop prevention: track resolved directory paths
            try:
                real = str(current.resolve())
            except OSError:
                skipped.append(
                    {
                        "path": str(current.relative_to(root)),
                        "reason": "resolve_error",
                    }
                )
                return
            if real in visited_real_paths:
                skipped.append(
                    {
                        "path": str(current.relative_to(root)),
                        "reason": "symlink_loop",
                    }
                )
                return
            visited_real_paths.add(real)

            rel_path = str(current.relative_to(root))

            if rel_path != ".":
                if exclude_spec and exclude_spec.match_file(rel_path + "/"):
                    return
                if is_ignored(rel_path, True, specs):
                    return
                directories.append(rel_path)

            # Load nested .gitignore (root already loaded into root_spec)
            child_specs = specs
            if rel_path != ".":
                nested_patterns = load_gitignore(current)
                if nested_patterns:
                    nested_spec = pathspec.PathSpec.from_lines(
                        "gitwildmatch", nested_patterns
                    )
                    child_specs = specs + [(rel_path, nested_spec)]

            try:
                entries = sorted(
                    current.iterdir(),
                    key=lambda p: (not p.is_dir(), p.name.lower()),
                )
                for entry in entries:
                    walk(entry, child_specs, depth + 1)
            except PermissionError:
                skipped.append({"path": rel_path, "reason": "permission_denied"})

        elif current.is_file():
            rel_path = str(current.relative_to(root))

            if exclude_spec and exclude_spec.match_file(rel_path):
                return
            if is_ignored(rel_path, False, specs):
                return

            size_bytes = current.stat().st_size

            # Skip very large files
            if size_bytes > 1_000_000:  # 1MB
                skipped.append(
                    {
                        "path": rel_path,
                        "reason": "too_large",
                        "size_bytes": size_bytes,
                    }
                )
                return

            if not is_text_file(current):
                skipped.append({"path": rel_path, "reason": "binary"})
                return

            try:
                with open(current, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                tokens = count_tokens(content, encoding)

                if tokens > max_file_tokens:
                    skipped.append(
                        {
                            "path": rel_path,
                            "reason": "too_many_tokens",
                            "tokens": tokens,
                        }
                    )
                    return

                files.append(
                    {
                        "path": rel_path,
                        "tokens": tokens,
                        "size_bytes": size_bytes,
                    }
                )
                total_tokens += tokens

            except Exception as e:
                skipped.append(
                    {"path": rel_path, "reason": f"read_error: {str(e)}"}
                )

    walk(root, [(".", root_spec)])

    return {
        "root": str(root),
        "files": files,
        "directories": directories,
        "total_tokens": total_tokens,
        "total_files": len(files),
        "skipped": skipped,
    }


def format_tree(scan_result: dict, show_tokens: bool = True) -> str:
    """Format scan results as a tree structure."""
    lines = []
    root_name = Path(scan_result["root"]).name
    lines.append(f"{root_name}/")
    lines.append(
        f"Total: {scan_result['total_files']} files, {scan_result['total_tokens']:,} tokens"
    )
    lines.append("")

    # Build tree structure
    tree: dict = {}
    for f in scan_result["files"]:
        parts = Path(f["path"]).parts
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        # Store file info
        current[parts[-1]] = f

    def print_tree(node: dict, prefix: str = "", is_last: bool = True):
        items = sorted(
            node.items(),
            key=lambda x: (
                not isinstance(x[1], dict) or "tokens" in x[1],
                x[0].lower(),
            ),
        )

        for i, (name, value) in enumerate(items):
            is_last_item = i == len(items) - 1
            connector = "\u2514\u2500\u2500 " if is_last_item else "\u251c\u2500\u2500 "

            if isinstance(value, dict) and "tokens" not in value:
                # Directory
                lines.append(f"{prefix}{connector}{name}/")
                extension = "    " if is_last_item else "\u2502   "
                print_tree(value, prefix + extension, is_last_item)
            else:
                # File
                if show_tokens:
                    tokens = value.get("tokens", 0)
                    lines.append(
                        f"{prefix}{connector}{name} ({tokens:,} tokens)"
                    )
                else:
                    lines.append(f"{prefix}{connector}{name}")

    print_tree(tree)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Scan a codebase and output file paths with token counts"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "tree", "compact"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=50000,
        help="Skip files with more than this many tokens (default: 50000)",
    )
    parser.add_argument(
        "--encoding",
        default="cl100k_base",
        help="Tiktoken encoding to use (default: cl100k_base)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Exclude paths matching pattern (gitignore format). Repeatable.",
    )

    args = parser.parse_args()
    path = Path(args.path).resolve()

    if not path.exists():
        print(f"ERROR: Path does not exist: {path}", file=sys.stderr)
        sys.exit(1)

    if not path.is_dir():
        print(f"ERROR: Path is not a directory: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        encoding = tiktoken.get_encoding(args.encoding)
    except Exception as e:
        print(
            f"ERROR: Failed to load encoding '{args.encoding}': {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    result = scan_directory(path, encoding, args.max_tokens, args.exclude)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "tree":
        print(format_tree(result, show_tokens=True))
    elif args.format == "compact":
        # Compact format: just paths and tokens, sorted by tokens descending
        files_sorted = sorted(
            result["files"], key=lambda x: x["tokens"], reverse=True
        )
        print(f"# {result['root']}")
        print(
            f"# Total: {result['total_files']} files, {result['total_tokens']:,} tokens"
        )
        print()
        for f in files_sorted:
            print(f"{f['tokens']:>8} {f['path']}")


if __name__ == "__main__":
    main()

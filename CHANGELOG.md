# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-25

### Added

- **Core engine:** Semantic document comparison for Microsoft Word (.docx)
  - Vector-based block matching using `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - Cosine similarity with configurable threshold (default 0.75)
  - Detects modified, moved, added, and removed blocks
- **Parser:** DOCX extraction with hierarchy preservation
  - Supports formal Heading 1–3 styles and heuristic detection (font size + bold + alignment)
  - Extracts tables as plain text blocks
  - Preserves metadata: style, bold, alignment, list type, font size
- **Diff engine:** Sentence-level comparison
  - `difflib.SequenceMatcher` for word-level changes
  - Automatic numeric change detection (digits, percentages, decimals)
- **Output formats:**
  - **HTML report:** Interactive side-by-side diff with dark/light theme, filter buttons, collapsible blocks, scroll spy TOC, and responsive design
  - **Markdown:** Human-readable terminal output
  - **JSON:** Structured data with metadata and summary counts
- **Interfaces:**
  - **CLI:** `docdiff` with `--format`, `--threshold`, `--device`, `--output` flags
  - **Web app:** FastAPI-based drag-and-drop UI (`docdiff-web` / `python -m docdiff.webapp.app`)
  - **Desktop GUI:** Self-contained launcher that starts server and opens browser (`docdiff-gui` / `python -m docdiff.desktop.launcher`)
  - **Windows .exe:** PyInstaller build (`build.py`) producing `docdiff.exe` and `docdiff-cli.exe`
- **Test suite:** 28 tests covering parser, differ, matcher, formatter, HTML generator, CLI, and web app endpoints
- **Documentation:** README with usage examples, architecture diagram, and build instructions

### Known Limitations

- First run downloads the ~120 MB sentence-transformers model (cached afterwards)
- Processing speed for 50+ page documents is CPU-bound (~30–60 seconds on average hardware)
- No native PDF support (convert DOCX to DOCX for comparison)

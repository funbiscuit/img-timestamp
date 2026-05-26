# imgts

CLI tool that batch-renames photos/videos by embedded timestamps. Python 3.10+.

## Commands

```bash
# Install (from project root)
pip install ".[dev]"          # with dev deps (mypy, pytest, ruff)
pip install ".[video]"        # with pymediainfo for accurate video dates

# Check (format + lint + typecheck)
./check.sh                     # check only
./check.sh --fix               # auto-fix format and lint

# Run tests
.venv/bin/pytest

# Run single test file
.venv/bin/pytest tests/test_filename_extractor.py

# Run single test by name
.venv/bin/pytest tests/test_edge_cases.py::TestCollisions::test_collision_burst_100_files
```

**Toolchain order:** `check.sh` runs mypy → ruff format → ruff check (not tests). Run pytest separately.

## Architecture

```
src/imgts/
├── __main__.py          # entry point, exception handling, cursor restore
├── cli.py               # typer app, full workflow orchestration (scan → extract → plan → apply)
├── models.py            # dataclasses: FileInfo, RenameAction, Plan, ScanStats, etc.
├── constants.py         # extensions, EXIF tag IDs, filename regex patterns, plan config
├── utils.py             # EXIF datetime parsing, target name formatting, year validation
├── errors.py            # ExitAppError (message + exit code)
└── services/
    ├── extractors/
    │   ├── __init__.py  # orchestrates all extractors per file type
    │   ├── exif_extractor.py      # Pillow EXIF (DateTimeOriginal/Digitized/Modify)
    │   ├── filesystem_extractor.py # st_birthtime (macOS) / st_mtime fallback
    │   ├── filename_extractor.py  # 10 regex patterns: iOS/Android screenshots, Telegram, WeChat, generic
    │   └── video_extractor.py     # pymediainfo (QuickTime creation_date) → mvhd atom fallback
    ├── info/            # Rich-based UI layer (spinners, prompts, tables, status messages)
    ├── scanner.py       # non-recursive directory scan, classifies by extension
    ├── renamer.py       # builds rename actions with collision handling, applies renames
    ├── metadata_writer.py  # writes EXIF + filesystem mtime on photos; mtime only on videos
    ├── plan_io.py       # JSON plan persistence (save/load/validate/delete)
    ├── stats.py         # coverage stats per source, interactive source selection
    └── fallback.py      # cascading fallback for unresolved files
```

**Entry point:** `imgts.__main__:main` (registered as `imgts` console script).

## Key Conventions

- **Package layout:** src-layout (`src/imgts/`). Package dir is `src`, not project root.
- **mypy:** strict mode, `python_version = "3.10"`, `mypy_path = ["src"]`.
- **ruff:** target py310, line-length 120, single quotes, spaces, LF line endings. Rules: E/W/F/I/B/C4/UP/SIM. E501
  ignored.
- **Version:** managed by `setuptools-scm` → writes to `src/imgts/_version.py` (gitignored).
- **Optional dep:** `pymediainfo` is runtime-optional with graceful fallback (`_HAS_MEDIAINFO` flag).
- **Error handling:** Extractors return `[]` on any failure (never raise). App-level errors use `ExitAppError`.
- **Tests:** `tests/` with pytest fixtures in `conftest.py`, test helpers in `helpers.py`. CLI tests use `subprocess`
  against `.venv/bin/imgts`.
- **No CI, no pre-commit hooks.** `check.sh` is the manual quality gate.

## Gotchas

- `pillow-heif` registration happens at import time in `exif_extractor.py` via `register_heif_opener()`.
- `video_extractor.py` falls back to raw binary `mvhd` atom parsing when `pymediainfo` is absent — this uses Mac epoch (
  1904-01-01), not Unix epoch.
- Year validation accepts 1970 through `current_year + 1` — dates outside this range are silently dropped.
- The plan file (`imgts-plan.json`) is written to the scanned directory, not the project root.
- `FS_CREATION` on Linux is actually `st_mtime` (no true birthtime support).

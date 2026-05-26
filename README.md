# imgts

> **Disclaimer:** This tool was written entirely with AI assistance. Use with caution.

CLI tool that batch-renames photos and videos by their embedded timestamps. Two-step workflow: dry-run to preview, then
apply changes with confirmation.

## Installation

```bash
pip install .

# With video metadata support (MP4/MOV accurate dates):
pip install ".[video]"

# With dev dependencies:
pip install ".[dev]"
```

Python >= 3.10 required.

## Dependencies

- **Runtime:** typer, rich, pillow, pillow-heif
- **Optional video:** pymediainfo

## Supported Formats

**Photos:** jpg, jpeg, png, tiff, tif, heic, heif, webp

**Videos:** mp4, mov, avi, mkv (video metadata extraction for mp4/mov)

## Date Sources

1. EXIF DateTimeOriginal (camera capture date)
2. EXIF DateTimeDigitized
3. EXIF DateTime (modification)
4. Filesystem creation time
5. Filesystem modification time
6. Filename patterns (iOS screenshots, Android screenshots, Telegram, WeChat, generic formats, 14-digit timestamps)
7. Video metadata (QuickTime creation_date / mvhd atom)

## CLI Usage

```bash
imgts                              # Dry-run: scan, pick source, preview, save plan
imgts --directory /path/to/photos  # Same, but for a specific directory
imgts --apply                      # Load plan (or build new), confirm [y/n/r], execute
```

**Options:**

- `--apply` — Apply changes (default: dry-run)
- `--directory` — Directory to scan (default: `.`)

## Workflow

1. `imgts` scans directory, extracts dates from all sources, shows coverage table per source
2. User picks a date source interactively
3. Tool builds rename plan, shows preview table, saves plan to `imgts-plan.json`
4. `imgts --apply` loads plan, shows preview, asks `[y/n/r]`
    - `y` — rename files and update metadata
    - `n` — cancel
    - `r` — rescan and rebuild plan (loops back to step 1)

## Output Naming

- **Photos:** `IMG_YYYYMMDD_HHMMSS.ext`
- **Videos:** `VID_YYYYMMDD_HHMMSS.ext`
- **Collisions:** `IMG_YYYYMMDD_HHMMSS_2.ext`

## Metadata Written

- **Photos:** EXIF DateTimeOriginal, DateTimeDigitized, DateTime + filesystem mtime
- **Videos:** filesystem mtime

## Key Features

- Idempotent: skips files already in target format
- Collision handling: auto-appends incrementing suffix
- Plan persistence: review before applying
- Cascading fallback for files missing the chosen source's date
- Non-recursive scanning, hidden files skipped
- Year validation: 1970–current+1

## Exit Codes

- `0` — success
- `1` — some files couldn't be resolved
- `2` — directory not found / not accessible

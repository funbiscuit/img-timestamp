"""Utility functions for imgts package."""

import os
from datetime import datetime

from imgts.constants import (
    MIN_VALID_YEAR,
    TARGET_NAME_RE,
)
from imgts.errors import ExitAppError
from imgts.models import FileType


def parse_exif_datetime(raw: str) -> datetime | None:
    """Parse EXIF datetime string to datetime object."""
    try:
        dt = datetime.strptime(raw, '%Y:%m:%d %H:%M:%S')
        if not validate_year(dt):
            return None
        return dt
    except (ValueError, TypeError):
        return None


def validate_year(dt: datetime) -> bool:
    """Check if datetime year is valid."""
    current_year = datetime.now().year
    return MIN_VALID_YEAR <= dt.year <= current_year + 1


def format_target_name(
    dt: datetime,
    ext: str,
    suffix: int | None = None,
    file_type: FileType = FileType.PHOTO,
) -> str:
    """Format datetime to target filename.

    Uses 'IMG_' prefix for photos, 'VID_' for videos.
    """
    prefix = 'VID_' if file_type is FileType.VIDEO else 'IMG_'
    base = dt.strftime(f'{prefix}%Y%m%d_%H%M%S')
    if suffix is not None:
        return f'{base}_{suffix}.{ext}'
    return f'{base}.{ext}'


def is_target_format(filename: str) -> bool:
    """Check if filename matches target format."""
    return TARGET_NAME_RE.match(filename) is not None


def parse_target_name(filename: str) -> datetime | None:
    """Extract datetime from target format filename."""
    match = TARGET_NAME_RE.match(filename)
    if not match:
        return None

    year, month, day, hour, minute, second = map(int, match.groups())
    dt = datetime(year, month, day, hour, minute, second)

    if not validate_year(dt):
        return None

    return dt


def safe_stat(path: str) -> os.stat_result:
    """Get file stat with error handling."""
    try:
        return os.stat(path)
    except OSError as e:
        raise ExitAppError(f'Cannot stat file: {path}: {e}') from e


def get_creation_time(stat_result: os.stat_result) -> datetime:
    """Get creation time from stat result."""
    # st_birthtime is available on macOS/BSD
    birthtime = getattr(stat_result, 'st_birthtime', None)
    if birthtime is not None:
        return datetime.fromtimestamp(birthtime)
    return datetime.fromtimestamp(stat_result.st_mtime)

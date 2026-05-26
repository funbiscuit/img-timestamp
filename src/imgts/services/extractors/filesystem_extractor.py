from datetime import datetime
from pathlib import Path

from imgts.models import DateSource, ExtractedDate
from imgts.utils import get_creation_time, validate_year


def extract_filesystem_dates(path: Path) -> list[ExtractedDate]:
    """Extract creation and modification dates from filesystem.

    Uses st_birthtime on macOS/BSD, falls back to st_mtime on Linux.
    Returns empty list on any error (file not found, permission denied, etc.).
    """
    try:
        stat = path.stat()
    except OSError:
        return []

    results: list[ExtractedDate] = []

    try:
        creation_dt = get_creation_time(stat)
        if validate_year(creation_dt):
            results.append(
                ExtractedDate(
                    source=DateSource.FS_CREATION,
                    datetime=creation_dt,
                )
            )
    except (OSError, ValueError, OverflowError):
        pass

    try:
        mod_dt = datetime.fromtimestamp(stat.st_mtime)
        if validate_year(mod_dt):
            results.append(
                ExtractedDate(
                    source=DateSource.FS_MODIFICATION,
                    datetime=mod_dt,
                )
            )
    except (OSError, ValueError, OverflowError):
        pass

    return results

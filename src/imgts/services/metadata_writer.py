"""EXIF write-back and filesystem timestamp updates."""

import os
from datetime import datetime
from pathlib import Path

from PIL import ExifTags, Image

from imgts.constants import EXIF_DATETIME, EXIF_DATETIME_DIGITIZED, EXIF_DATETIME_ORIGINAL, PHOTO_EXTENSIONS
from imgts.models import RenameAction
from imgts.services import info


def update_metadata(path: Path, dt: datetime, dry_run: bool = True) -> bool:
    """Update ALL available dates on a file to the given datetime.

    Updates EXIF data (photos only) and filesystem timestamps.
    Returns True if successful, False if any errors occurred.
    """
    if dry_run:
        return True

    success = True
    exif_str = dt.strftime('%Y:%m:%d %H:%M:%S')

    ext = path.suffix.lstrip('.').lower()
    if ext in PHOTO_EXTENSIONS:
        try:
            img = Image.open(path)
            exif = img.getexif()

            exif[EXIF_DATETIME] = exif_str

            ifd_exif = exif.get_ifd(ExifTags.IFD.Exif)
            ifd_exif[EXIF_DATETIME_ORIGINAL] = exif_str
            ifd_exif[EXIF_DATETIME_DIGITIZED] = exif_str
            exif[ExifTags.IFD.Exif] = ifd_exif

            img.save(str(path), exif=exif.tobytes())
        except Exception as e:
            info.warn(f'Failed to update EXIF for {path.name}: {e}')
            success = False

    try:
        mtime = dt.timestamp()
        os.utime(str(path), (mtime, mtime))
    except OSError as e:
        info.warn(f'Failed to set filesystem time for {path.name}: {e}')
        success = False

    return success


def update_all_metadata(
    actions: list[RenameAction],
    dry_run: bool = True,
) -> tuple[int, int]:
    """Update metadata for all rename actions.

    Uses the new_path and datetime from each RenameAction.
    Returns (updated_count, failed_count).
    """
    updated = 0
    failed = 0

    for action in actions:
        if update_metadata(action.new_path, action.datetime, dry_run=dry_run):
            updated += 1
        else:
            failed += 1

    return updated, failed

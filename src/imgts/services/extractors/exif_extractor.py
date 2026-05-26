# ruff: noqa: I001
"""EXIF date extraction using Pillow."""

from pathlib import Path

from PIL import ExifTags, Image

# Try to register HEIF support
try:
    from pillow_heif import register_heif_opener  # type: ignore[import-untyped]

    register_heif_opener()
except ImportError:
    pass

from imgts.constants import EXIF_DATETIME, EXIF_DATETIME_DIGITIZED, EXIF_DATETIME_ORIGINAL
from imgts.models import DateSource, ExtractedDate
from imgts.utils import parse_exif_datetime  # noqa: I001


def extract_exif_dates(path: Path) -> list[ExtractedDate]:
    """Extract dates from EXIF metadata.

    Reads DateTimeOriginal (0x9003), DateTimeDigitized (0x9004) from ExifIFD sub-IFD,
    and DateTime (0x0132) from IFD0.
    Returns empty list on any error (corrupt file, no EXIF, invalid dates).
    """
    try:
        img = Image.open(path)
        exif = img.getexif()

        results: list[ExtractedDate] = []

        # Get ExifIFD sub-IFD for DateTimeOriginal and DateTimeDigitized
        ifd_exif = exif.get_ifd(ExifTags.IFD.Exif)

        # DateTimeOriginal (0x9003) — camera capture date
        raw_original = ifd_exif.get(EXIF_DATETIME_ORIGINAL)
        if raw_original and isinstance(raw_original, str):
            dt = parse_exif_datetime(raw_original)
            if dt is not None:
                results.append(
                    ExtractedDate(
                        source=DateSource.EXIF_ORIGINAL,
                        datetime=dt,
                        raw_value=raw_original,
                    )
                )

        # DateTimeDigitized (0x9004) — digitization date
        raw_digitized = ifd_exif.get(EXIF_DATETIME_DIGITIZED)
        if raw_digitized and isinstance(raw_digitized, str):
            dt = parse_exif_datetime(raw_digitized)
            if dt is not None:
                results.append(
                    ExtractedDate(
                        source=DateSource.EXIF_DIGITIZED,
                        datetime=dt,
                        raw_value=raw_digitized,
                    )
                )

        # DateTime (0x0132) — IFD0 modification date
        raw_datetime = exif.get(EXIF_DATETIME)
        if raw_datetime and isinstance(raw_datetime, str):
            dt = parse_exif_datetime(raw_datetime)
            if dt is not None:
                results.append(
                    ExtractedDate(
                        source=DateSource.EXIF_MODIFY,
                        datetime=dt,
                        raw_value=raw_datetime,
                    )
                )

        return results
    except Exception:
        return []

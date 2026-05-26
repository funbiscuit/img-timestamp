import struct
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from imgts.constants import MAC_EPOCH, VIDEO_WITH_METADATA
from imgts.models import DateSource, ExtractedDate
from imgts.utils import validate_year


_HAS_MEDIAINFO = False

try:
    from pymediainfo import MediaInfo

    MediaInfo.can_parse()
    _HAS_MEDIAINFO = True
except (ImportError, OSError):
    MediaInfo: Any = None  # type: ignore[no-redef]


def _mac_epoch_to_datetime(timestamp: int) -> datetime:
    """Convert Mac epoch (seconds since 1904-01-01) to datetime."""
    return MAC_EPOCH + timedelta(seconds=timestamp)


def _extract_mediainfo_date(path: Path) -> list[ExtractedDate]:
    """Extract video date using pymediainfo.

    Prioritizes com.apple.quicktime.creationdate (most accurate for iPhone videos).
    Falls back to tagged_date if QuickTime metadata not available.
    Returns empty list if extraction fails.
    """
    if not _HAS_MEDIAINFO or MediaInfo is None:
        return []

    try:
        media_info = MediaInfo.parse(path)

        for track in media_info.tracks:
            if track.track_type == 'General':
                qt_creation_date = getattr(track, 'comapplequicktimecreationdate', None)
                if qt_creation_date:
                    dt = _parse_iso_datetime(qt_creation_date)
                    if dt and validate_year(dt):
                        return [
                            ExtractedDate(
                                source=DateSource.VIDEO_METADATA,
                                datetime=dt,
                            )
                        ]

                tagged_date = getattr(track, 'tagged_date', None)
                if tagged_date:
                    dt = _parse_iso_datetime(tagged_date)
                    if dt and validate_year(dt):
                        return [
                            ExtractedDate(
                                source=DateSource.VIDEO_METADATA,
                                datetime=dt,
                            )
                        ]

        return []
    except Exception:
        return []


def _parse_iso_datetime(date_str: str) -> datetime | None:
    """Parse ISO datetime string to naive local datetime.

    Handles timezone-aware strings like "2026-05-23T10:15:20+0300"
    by converting to naive local time.
    """
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None


def extract_video_date(path: Path) -> list[ExtractedDate]:
    """Extract creation date from MP4/MOV files.

    Only processes mp4 and mov files (VIDEO_WITH_METADATA).
    Tries pymediainfo first (for accurate QuickTime metadata with timezone),
    falls back to mvhd atom parsing if pymediainfo unavailable or fails.
    Returns empty list for unsupported formats or on any error.
    """
    ext = path.suffix.lstrip('.').lower()
    if ext not in VIDEO_WITH_METADATA:
        return []

    if _HAS_MEDIAINFO:
        mediainfo_dates = _extract_mediainfo_date(path)
        if mediainfo_dates:
            return mediainfo_dates

    return _extract_mvhd_date(path)


def _extract_mvhd_date(path: Path) -> list[ExtractedDate]:
    """Extract creation date from MP4/MOV mvhd atom (fallback method).

    Searches for 'mvhd' atom in binary data, reads creation_time,
    converts from Mac epoch (1904) to datetime.
    Returns empty list for unsupported formats or on any error.
    """

    try:
        with open(path, 'rb') as f:
            data = f.read()

        idx = data.find(b'mvhd')
        if idx == -1:
            return []

        version_offset = idx + 4
        if version_offset + 4 > len(data):
            return []

        version_byte = data[version_offset]

        if version_byte == 0:
            time_offset = version_offset + 4
            if time_offset + 4 > len(data):
                return []
            creation_time = struct.unpack('>I', data[time_offset : time_offset + 4])[0]
        elif version_byte == 1:
            time_offset = version_offset + 4
            if time_offset + 8 > len(data):
                return []
            creation_time = struct.unpack('>Q', data[time_offset : time_offset + 8])[0]
        else:
            return []

        dt = _mac_epoch_to_datetime(creation_time)

        if not validate_year(dt):
            return []

        return [
            ExtractedDate(
                source=DateSource.VIDEO_METADATA,
                datetime=dt,
            )
        ]
    except Exception:
        return []

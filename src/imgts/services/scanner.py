"""Directory scanning and file type detection."""

import os
from pathlib import Path

from imgts.constants import ALL_SUPPORTED_EXTENSIONS, PHOTO_EXTENSIONS, VIDEO_EXTENSIONS
from imgts.models import FileInfo, FileType, ScanResult
from imgts.utils import safe_stat


def get_extension(path: os.PathLike[str] | str) -> str:
    """Return lowercase file extension without dot."""
    name = os.path.basename(str(path))
    if '.' not in name:
        return ''
    return name.rsplit('.', 1)[-1].lower()


def classify_file(path: os.PathLike[str] | str) -> FileType | None:
    """Classify file by extension. Returns None if not supported."""
    ext = get_extension(path)
    if ext in PHOTO_EXTENSIONS:
        return FileType.PHOTO
    if ext in VIDEO_EXTENSIONS:
        return FileType.VIDEO
    return None


def scan_directory(directory: os.PathLike[str] | str) -> ScanResult:
    """Scan directory non-recursively, classify files by type.

    Skips hidden files (starting with '.').
    """
    directory = os.fspath(directory)
    photos: list[FileInfo] = []
    videos: list[FileInfo] = []
    skipped: list[Path] = []

    for entry in sorted(os.scandir(directory), key=lambda e: e.name):
        if entry.name.startswith('.'):
            continue
        if not entry.is_file():
            continue

        path_str = entry.path
        ext = get_extension(path_str)

        if ext not in ALL_SUPPORTED_EXTENSIONS:
            skipped.append(Path(path_str))
            continue

        file_type = classify_file(path_str)
        if file_type is None:
            skipped.append(Path(path_str))
            continue

        try:
            stat = safe_stat(path_str)
            size = stat.st_size
        except Exception:
            continue

        file_info = FileInfo(
            path=Path(path_str),
            file_type=file_type,
            extension=ext,
            dates=[],
            size=size,
        )

        if file_type is FileType.PHOTO:
            photos.append(file_info)
        else:
            videos.append(file_info)

    return ScanResult(photos=photos, videos=videos, skipped=skipped)

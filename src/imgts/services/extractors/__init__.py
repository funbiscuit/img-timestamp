from imgts.models import FileInfo, FileType
from imgts.services import info
from imgts.services.extractors.exif_extractor import extract_exif_dates
from imgts.services.extractors.filename_extractor import extract_filename_date
from imgts.services.extractors.filesystem_extractor import extract_filesystem_dates
from imgts.services.extractors.video_extractor import _HAS_MEDIAINFO, extract_video_date

_MEDIAINFO_WARNED = False


def extract_all_dates(file_info: FileInfo) -> FileInfo:
    """Extract dates from all applicable sources for a file.

    Photos: EXIF + filesystem + filename
    Videos: video metadata + filesystem + filename
    """
    global _MEDIAINFO_WARNED

    if file_info.file_type is FileType.PHOTO:
        file_info.dates.extend(extract_exif_dates(file_info.path))
    elif file_info.file_type is FileType.VIDEO:
        if not _HAS_MEDIAINFO and not _MEDIAINFO_WARNED:
            info.warn(
                'pymediainfo not available — video dates from mvhd may be inaccurate. '
                'Install with: pip install pymediainfo'
            )
            _MEDIAINFO_WARNED = True
        file_info.dates.extend(extract_video_date(file_info.path))

    # All types: filesystem + filename
    file_info.dates.extend(extract_filesystem_dates(file_info.path))
    file_info.dates.extend(extract_filename_date(file_info.path))

    return file_info


def extract_dates_for_files(files: list[FileInfo]) -> list[FileInfo]:
    """Extract dates for all files, showing a spinner."""
    with info.status('Extracting dates...'):
        return [extract_all_dates(f) for f in files]

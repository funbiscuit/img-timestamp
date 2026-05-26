import os
import struct
import time
from datetime import datetime
from pathlib import Path

from PIL import Image


def create_test_image(
    path: str | Path,
    format: str = 'JPEG',
    exif_datetime: str | None = None,
) -> Path:
    """Create a minimal test image with optional EXIF data.

    Args:
        path: Output file path
        format: PIL format (JPEG, PNG, etc.)
        exif_datetime: EXIF datetime string like '2024:05:26 14:30:00'

    Returns:
        Path to the created image
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new('RGB', (10, 10), color='red')

    if exif_datetime and format.upper() in ('JPEG', 'TIFF'):
        exif = img.getexif()
        # DateTime (0x0132) in IFD0
        exif[0x0132] = exif_datetime

        # DateTimeOriginal (0x9003) and DateTimeDigitized (0x9004) in ExifIFD sub-IFD
        from PIL.ExifTags import IFD
        exif_ifd = exif.get_ifd(IFD.Exif) if hasattr(exif, 'get_ifd') else {}
        exif_ifd[0x9003] = exif_datetime  # DateTimeOriginal
        exif_ifd[0x9004] = exif_datetime  # DateTimeDigitized
        exif[IFD.Exif] = exif_ifd

        img.save(str(path), format, exif=exif.tobytes())
    else:
        img.save(str(path), format)

    return path


def create_test_video(
    path: str | Path,
    creation_time: datetime | None = None,
) -> Path:
    """Create a minimal MP4 file with mvhd atom.

    Args:
        path: Output file path
        creation_time: Creation datetime (default: 2024-05-26 14:30:00)

    Returns:
        Path to the created video file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if creation_time is None:
        creation_time = datetime(2024, 5, 26, 14, 30, 0)

    mac_epoch = datetime(1904, 1, 1)
    mac_seconds = int((creation_time - mac_epoch).total_seconds())

    # Build mvhd atom (version 0)
    # [size:4][type:4='mvhd'][version:1][flags:3][creation:4][modification:4][timescale:4][duration:4]...+padding
    version_flags = struct.pack('>I', 0)  # version 0, flags 0
    creation = struct.pack('>I', mac_seconds)
    modification = struct.pack('>I', mac_seconds)
    timescale = struct.pack('>I', 1000)
    duration = struct.pack('>I', 0)
    # mvhd has additional fields: rate(4), volume(2), reserved(10), matrix(36), predefined(24), next_track_id(4) = 80 bytes
    padding = b'\x00' * 80

    mvhd_body = b'mvhd' + version_flags + creation + modification + timescale + duration + padding
    atom_size = struct.pack('>I', len(mvhd_body) + 4)
    mvhd_atom = atom_size + mvhd_body

    with open(path, 'wb') as f:
        f.write(mvhd_atom)

    return path


def set_fs_times(
    path: str | Path,
    creation: float | None = None,
    modification: float | None = None,
) -> None:
    """Set filesystem timestamps for a file.

    Args:
        path: File path
        creation: Creation time as Unix timestamp (may not work on all platforms)
        modification: Modification time as Unix timestamp
    """
    path = Path(path)
    atime = modification if modification else time.time()
    mtime = modification if modification else time.time()
    os.utime(str(path), (atime, mtime))


def create_files_in_dir(
    directory: str | Path,
    specs: list[dict[str, str | None]],
) -> list[Path]:
    """Create files in a directory from specifications.

    Args:
        directory: Target directory
        specs: List of dicts with keys: 'name', 'content' (optional), 'type' ('image'|'video'|'text')

    Returns:
        List of created file paths
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    for spec in specs:
        name = spec.get('name')
        if name is None:
            raise ValueError("spec must contain 'name' key")
        path = directory / name
        file_type = spec.get('type', 'text')

        if file_type == 'image':
            exif_dt = spec.get('exif_datetime')
            create_test_image(path, format='JPEG', exif_datetime=exif_dt)
        elif file_type == 'video':
            create_test_video(path)
        else:
            content = spec.get('content', '')
            path.write_text(str(content))

        created.append(path)

    return created

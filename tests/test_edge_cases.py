import os
from datetime import datetime
from pathlib import Path

import pytest

from imgts.models import DateSource, FileInfo, FileType, ExtractedDate
from imgts.services.extractors.exif_extractor import extract_exif_dates
from imgts.services.extractors.filename_extractor import extract_filename_date
from imgts.services.extractors.filesystem_extractor import extract_filesystem_dates
from imgts.services.renamer import build_rename_actions
from imgts.services.scanner import scan_directory
from tests.helpers import create_test_image


class TestZeroByteFiles:
    """Zero-byte and minimal file handling."""

    def test_zero_byte_jpeg_no_crash(self, tmp_path):
        """Zero-byte .jpg doesn't crash extractor."""
        p = tmp_path / 'empty.jpg'
        p.write_bytes(b'')
        dates = extract_exif_dates(p)
        assert dates == []

    def test_tiny_file(self, tmp_path):
        """Very small file (1 byte) doesn't crash."""
        p = tmp_path / 'tiny.jpg'
        p.write_bytes(b'x')
        dates = extract_exif_dates(p)
        assert dates == []


class TestCorruptFiles:
    """Corrupt file handling."""

    def test_corrupt_jpeg_no_crash(self, tmp_path):
        """Random bytes as JPEG doesn't crash."""
        p = tmp_path / 'corrupt.jpg'
        p.write_bytes(os.urandom(100))
        dates = extract_exif_dates(p)
        assert dates == []

    def test_partial_exif_data_no_crash(self, tmp_path):
        """Partial/truncated EXIF data doesn't crash."""
        p = tmp_path / 'partial.jpg'
        p.write_bytes(b'\xff\xd8\xff\xe1' + b'\x00' * 50)
        dates = extract_exif_dates(p)
        assert dates == []


class TestFilesWithoutDates:
    """Files with no extractable dates."""

    def test_png_without_exif(self, tmp_path):
        """PNG without EXIF returns empty from EXIF extractor."""
        from PIL import Image
        img = Image.new('RGB', (1, 1))
        img.save(str(tmp_path / 'plain.png'), 'PNG')
        dates = extract_exif_dates(tmp_path / 'plain.png')
        assert dates == []

    def test_all_extractors_empty(self, tmp_path):
        """Text file has no dates from any extractor."""
        p = tmp_path / 'readme.txt'
        p.write_text('hello')
        assert extract_exif_dates(p) == []
        assert extract_filename_date(p) == []


class TestExifValidation:
    """EXIF date validation."""

    def test_exif_year_0000_rejected(self, tmp_path):
        """EXIF with year 0000 is rejected."""
        p = tmp_path / 'bad.jpg'
        create_test_image(str(p), exif_datetime='0000:01:01 00:00:00')
        dates = extract_exif_dates(p)
        assert dates == []

    def test_exif_year_1970_accepted(self, tmp_path):
        """EXIF with year 1970 is accepted (boundary)."""
        p = tmp_path / 'boundary.jpg'
        create_test_image(str(p), exif_datetime='1970:01:01 00:00:00')
        dates = extract_exif_dates(p)
        original = [d for d in dates if d.source == DateSource.EXIF_ORIGINAL]
        assert len(original) == 1
        assert original[0].datetime.year == 1970


class TestCollisions:
    """Filename collision resolution."""

    def test_collision_burst_100_files(self, tmp_path):
        """100 files with same date all get unique names."""
        dt = datetime(2024, 5, 26, 14, 30, 0)
        files = []
        for i in range(100):
            p = tmp_path / f'file_{i}.jpg'
            p.touch()
            files.append(FileInfo(
                path=p, file_type=FileType.PHOTO, extension='jpg',
                dates=[ExtractedDate(source=DateSource.FS_CREATION, datetime=dt)],
                size=0,
            ))

        actions, unresolved = build_rename_actions(files, DateSource.FS_CREATION)
        assert len(actions) == 100
        names = [a.new_path.name for a in actions]
        assert len(set(names)) == 100, 'Not all names are unique'

    def test_two_files_same_date(self, tmp_path):
        """Two files with same date get _0 and _1 (or no suffix + _1)."""
        dt = datetime(2024, 5, 26, 14, 30, 0)
        files = [
            FileInfo(path=tmp_path / 'a.jpg', file_type=FileType.PHOTO, extension='jpg',
                     dates=[ExtractedDate(source=DateSource.FS_CREATION, datetime=dt)], size=0),
            FileInfo(path=tmp_path / 'b.jpg', file_type=FileType.PHOTO, extension='jpg',
                     dates=[ExtractedDate(source=DateSource.FS_CREATION, datetime=dt)], size=0),
        ]
        actions, unresolved = build_rename_actions(files, DateSource.FS_CREATION)
        assert len(actions) == 2
        names = [a.new_path.name for a in actions]
        assert 'IMG_20240526_143000.jpg' in names
        assert 'IMG_20240526_143000_1.jpg' in names


class TestHiddenFiles:
    """Hidden file handling."""

    def test_hidden_file_skipped(self, tmp_path):
        """Files starting with . are skipped."""
        (tmp_path / '.hidden.jpg').touch()
        (tmp_path / 'normal.jpg').touch()
        result = scan_directory(tmp_path)
        assert len(result.photos) == 1
        assert len(result.skipped) == 0  # .hidden.jpg is skipped, not added to skipped


class TestExtensionCase:
    """Extension case insensitivity."""

    def test_uppercase_extension(self, tmp_path):
        """.JPG and .Jpeg recognized as photos."""
        from PIL import Image
        (tmp_path / 'photo.JPG').touch()
        img = Image.new('RGB', (1, 1))
        img.save(str(tmp_path / 'image.Jpeg'), 'JPEG')

        result = scan_directory(tmp_path)
        assert len(result.photos) == 2


class TestIdempotency:
    """Idempotency: re-processing already-renamed files."""

    def test_already_target_format_same_date(self, tmp_path):
        """File already in target format with correct date stays in actions (for metadata update)."""
        dt = datetime(2024, 5, 26, 14, 30, 0)
        files = [
            FileInfo(path=tmp_path / 'IMG_20240526_143000.jpg', file_type=FileType.PHOTO,
                     extension='jpg',
                     dates=[ExtractedDate(source=DateSource.EXIF_ORIGINAL, datetime=dt)], size=0),
        ]
        actions, unresolved = build_rename_actions(files, DateSource.EXIF_ORIGINAL)
        assert len(actions) == 1
        assert actions[0].original_path == actions[0].new_path

    def test_target_format_different_date_renames(self, tmp_path):
        """File in target format but different date gets renamed."""
        dt_old = datetime(2024, 5, 25, 12, 0, 0)
        dt_new = datetime(2024, 5, 26, 14, 30, 0)
        files = [
            FileInfo(path=tmp_path / 'IMG_20240525_120000.jpg', file_type=FileType.PHOTO,
                     extension='jpg',
                     dates=[ExtractedDate(source=DateSource.EXIF_ORIGINAL, datetime=dt_new)], size=0),
        ]
        actions, unresolved = build_rename_actions(files, DateSource.EXIF_ORIGINAL)
        assert len(actions) == 1  # Different date → needs rename

"""End-to-end integration tests."""

import os
from datetime import datetime
from pathlib import Path

import pytest
from PIL import ExifTags, Image

from imgts.models import DateSource
from imgts.services.extractors import extract_dates_for_files
from imgts.services.metadata_writer import update_all_metadata
from imgts.services.renamer import apply_renames, build_rename_actions
from imgts.services.scanner import scan_directory
from tests.helpers import create_test_image, create_test_video


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow_dry_run(self, tmp_path):
        """Test full workflow: scan → extract → build actions with dry_run=True."""
        # Create test files
        create_test_image(
            str(tmp_path / 'photo1.jpg'), exif_datetime='2024:05:26 14:30:00'
        )
        create_test_image(str(tmp_path / 'photo2.png'))  # no EXIF
        create_test_video(
            str(tmp_path / 'video1.mp4'),
            creation_time=datetime(2024, 5, 26, 10, 0, 0),
        )

        # Step 1: Scan
        result = scan_directory(tmp_path)
        assert len(result.photos) == 2
        assert len(result.videos) == 1

        # Step 2: Extract dates
        all_files = result.photos + result.videos
        all_files = extract_dates_for_files(all_files)

        # photo1.jpg should have EXIF dates + filesystem + filename
        photo1 = [f for f in all_files if f.path.name == 'photo1.jpg'][0]
        assert any(d.source == DateSource.EXIF_ORIGINAL for d in photo1.dates)

        # photo2.png should only have filesystem dates
        photo2 = [f for f in all_files if f.path.name == 'photo2.png'][0]
        assert any(d.source == DateSource.FS_CREATION for d in photo2.dates)

        # Step 3: Build rename actions using FS_CREATION (all files have it)
        actions, unresolved = build_rename_actions(all_files, DateSource.FS_CREATION)
        # photo1 and photo2 and video1 all have FS_CREATION
        assert len(actions) >= 3
        assert len(unresolved) == 0

    def test_full_workflow_apply(self, tmp_path):
        """Test apply: files get renamed and metadata updated."""
        dt = datetime(2024, 5, 26, 14, 30, 0)
        create_test_image(
            str(tmp_path / 'original.jpg'), exif_datetime='2020:01:01 00:00:00'
        )

        # Scan and extract
        result = scan_directory(tmp_path)
        all_files = extract_dates_for_files(result.photos + result.videos)

        # Rename using EXIF_ORIGINAL
        actions, unresolved = build_rename_actions(all_files, DateSource.EXIF_ORIGINAL)
        assert len(actions) == 1
        assert actions[0].original_path.name == 'original.jpg'
        assert actions[0].new_path.name == 'IMG_20200101_000000.jpg'

        # Apply renames
        renamed, skipped = apply_renames(actions, dry_run=False)
        assert renamed == 1
        assert skipped == 0

        # Verify file renamed
        assert (tmp_path / 'IMG_20200101_000000.jpg').exists()

        # Update metadata
        updated, failed = update_all_metadata(actions, dry_run=False)
        assert updated == 1
        assert failed == 0

        # Verify EXIF updated
        img = Image.open(tmp_path / 'IMG_20200101_000000.jpg')
        exif = img.getexif()
        exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
        assert exif_ifd.get(0x9003) == '2020:01:01 00:00:00'

    def test_idempotency(self, tmp_path):
        """Second run: file stays in actions but rename is skipped (paths equal)."""
        dt = datetime(2024, 5, 26, 14, 30, 0)
        create_test_image(
            str(tmp_path / 'photo.jpg'), exif_datetime='2024:05:26 14:30:00'
        )

        result = scan_directory(tmp_path)
        all_files = extract_dates_for_files(result.photos)

        # First run
        actions1, _ = build_rename_actions(all_files, DateSource.EXIF_ORIGINAL)
        assert len(actions1) == 1
        renamed1, _ = apply_renames(actions1, dry_run=False)
        assert renamed1 == 1

        # Second run (on already renamed file)
        result2 = scan_directory(tmp_path)
        all_files2 = extract_dates_for_files(result2.photos)
        actions2, _ = build_rename_actions(all_files2, DateSource.EXIF_ORIGINAL)
        assert len(actions2) == 1
        assert actions2[0].original_path == actions2[0].new_path
        renamed2, _ = apply_renames(actions2, dry_run=False)
        assert renamed2 == 0

    def test_video_mvhd_extraction(self, tmp_path):
        """Video with mvhd atom extracts correct date."""
        create_test_video(
            str(tmp_path / 'test.mp4'), creation_time=datetime(2024, 5, 26, 10, 0, 0)
        )

        result = scan_directory(tmp_path)
        all_files = extract_dates_for_files(result.videos)

        video = [f for f in all_files if f.path.name == 'test.mp4'][0]
        assert any(d.source == DateSource.VIDEO_METADATA for d in video.dates)

    def test_no_files_empty_dir(self, tmp_path):
        """Empty directory produces no results."""
        result = scan_directory(tmp_path)
        assert len(result.photos) == 0
        assert len(result.videos) == 0
        assert len(result.skipped) == 0

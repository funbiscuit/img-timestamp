"""Comprehensive unit tests for multi-pattern filename date extractor."""

from datetime import datetime
from pathlib import Path

from imgts.models import DateSource
from imgts.services.extractors.filename_extractor import extract_filename_date


class TestTargetFormat:
    """Target format: IMG_YYYYMMDD_HHMMSS and VID_YYYYMMDD_HHMMSS."""

    def test_img_target_format(self):
        """IMG_20240526_143000.jpg extracts datetime correctly."""
        dates = extract_filename_date(Path('IMG_20240526_143000.jpg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)
        assert dates[0].source == DateSource.FILENAME
        assert dates[0].raw_value == 'IMG_20240526_143000'

    def test_vid_target_format(self):
        """VID_20240526_143000.mp4 extracts datetime correctly."""
        dates = extract_filename_date(Path('VID_20240526_143000.mp4'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)
        assert dates[0].source == DateSource.FILENAME

    def test_target_format_with_suffix(self):
        """IMG_20240526_143000_1.jpg extracts datetime correctly with suffix."""
        dates = extract_filename_date(Path('IMG_20240526_143000_1.jpg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)
        assert dates[0].raw_value == 'IMG_20240526_143000_1'

    def test_year_before_1970_rejected(self):
        """IMG_19691231_235959.jpg rejected (year < 1970)."""
        dates = extract_filename_date(Path('IMG_19691231_235959.jpg'))
        assert dates == []

    def test_random_file_no_match(self):
        """random_file.jpg returns empty list (no pattern match)."""
        dates = extract_filename_date(Path('random_file.jpg'))
        assert dates == []


class TestIOSScreenshot:
    """iOS screenshot format: Screenshot YYYY-MM-DD at HH.MM.SS."""

    def test_ios_screenshot(self):
        """Screenshot 2024-05-26 at 14.30.00.png extracts datetime."""
        dates = extract_filename_date(Path('Screenshot 2024-05-26 at 14.30.00.png'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)
        assert dates[0].raw_value == 'Screenshot 2024-05-26 at 14.30.00'

    def test_ios_screenshot_midnight(self):
        """Screenshot 2024-05-26 at 00.00.00.png handles midnight."""
        dates = extract_filename_date(Path('Screenshot 2024-05-26 at 00.00.00.png'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 0, 0, 0)

    def test_ios_screenshot_invalid_date(self):
        """Screenshot 2024-02-30 at 10.00.00.png rejected (Feb 30 invalid)."""
        dates = extract_filename_date(Path('Screenshot 2024-02-30 at 10.00.00.png'))
        assert dates == []


class TestAndroidScreenshot:
    """Android screenshot format: Screenshot_YYYY-MM-DD-HH-MM-SS."""

    def test_android_screenshot(self):
        """Screenshot_2024-05-26-14-30-00.png extracts datetime."""
        dates = extract_filename_date(Path('Screenshot_2024-05-26-14-30-00.png'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)
        assert dates[0].raw_value == 'Screenshot_2024-05-26-14-30-00'


class TestTelegram:
    """Telegram format: photo_YYYY-MM-DD_HH-MM-SS."""

    def test_telegram_jpg(self):
        """photo_2024-05-26_14-30-00.jpg extracts datetime."""
        dates = extract_filename_date(Path('photo_2024-05-26_14-30-00.jpg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)
        assert dates[0].raw_value == 'photo_2024-05-26_14-30-00'

    def test_telegram_jpeg(self):
        """photo_2024-05-26_14-30-00.jpeg extracts datetime."""
        dates = extract_filename_date(Path('photo_2024-05-26_14-30-00.jpeg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)


class TestWeChat:
    """WeChat format: mmexport + 14 digits (YYYYMMDDHHMMSS)."""

    def test_wechat_format(self):
        """mmexport20240526143000.jpg extracts datetime (14-digit format, not timestamp)."""
        dates = extract_filename_date(Path('mmexport20240526143000.jpg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)
        assert dates[0].raw_value == 'mmexport20240526143000'


class TestGenericFormats:
    """Generic date-time formats in filenames."""

    def test_generic_dash_underscore(self):
        """2024-05-26_14-30-00.jpg extracts datetime."""
        dates = extract_filename_date(Path('2024-05-26_14-30-00.jpg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)

    def test_generic_underscore(self):
        """2024_05_26_14_30_00.jpg extracts datetime."""
        dates = extract_filename_date(Path('2024_05_26_14_30_00.jpg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)

    def test_generic_dot_dash(self):
        """2024.05.26-14.30.00.jpg extracts datetime."""
        dates = extract_filename_date(Path('2024.05.26-14.30.00.jpg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)

    def test_generic_dash_space(self):
        """photo 2024-05-26 14.30.00.jpg extracts datetime."""
        dates = extract_filename_date(Path('photo 2024-05-26 14.30.00.jpg'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)


class TestEdgeCases:
    """Edge cases and validation."""

    def test_invalid_month(self):
        """Month 13 rejected (invalid date)."""
        dates = extract_filename_date(Path('IMG_20241326_143000.jpg'))
        assert dates == []

    def test_invalid_day(self):
        """Day 32 rejected (invalid date)."""
        dates = extract_filename_date(Path('IMG_20240532_143000.jpg'))
        assert dates == []

    def test_far_future_year(self):
        """Year in far future rejected (year > current_year + 1)."""
        dates = extract_filename_date(Path('IMG_20990526_143000.jpg'))
        assert dates == []

    def test_empty_filename(self):
        """Empty filename returns empty list."""
        dates = extract_filename_date(Path(''))
        assert dates == []

    def test_priority_order_android_vs_generic(self):
        """Android screenshot has higher priority than generic_14digit."""
        # Screenshot_2024-05-26_14-30-00.png could match both android_screenshot
        # and generic_14digit (if underscores), but android should win
        dates = extract_filename_date(Path('Screenshot_2024-05-26-14-30-00.png'))
        assert len(dates) == 1
        assert dates[0].datetime == datetime(2024, 5, 26, 14, 30, 0)
        # Android pattern matches with dashes, so raw_value confirms priority
        assert dates[0].raw_value == 'Screenshot_2024-05-26-14-30-00'


class TestRawValue:
    """Verify raw_value is populated correctly for different patterns."""

    def test_raw_value_target_format(self):
        """Target format populates raw_value with full match."""
        dates = extract_filename_date(Path('IMG_20240526_143000.jpg'))
        assert len(dates) == 1
        assert dates[0].raw_value == 'IMG_20240526_143000'

    def test_raw_value_ios_screenshot(self):
        """iOS screenshot populates raw_value with full match."""
        dates = extract_filename_date(Path('Screenshot 2024-05-26 at 14.30.00.png'))
        assert len(dates) == 1
        assert dates[0].raw_value == 'Screenshot 2024-05-26 at 14.30.00'

    def test_raw_value_telegram(self):
        """Telegram format populates raw_value with full match."""
        dates = extract_filename_date(Path('photo_2024-05-26_14-30-00.jpg'))
        assert len(dates) == 1
        assert dates[0].raw_value == 'photo_2024-05-26_14-30-00'

    def test_raw_value_wechat(self):
        """WeChat format populates raw_value with mmexport + digits."""
        dates = extract_filename_date(Path('mmexport20240526143000.jpg'))
        assert len(dates) == 1
        assert dates[0].raw_value == 'mmexport20240526143000'

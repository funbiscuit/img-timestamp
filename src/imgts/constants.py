"""Constants for imgts package."""

import re
from datetime import datetime


PHOTO_EXTENSIONS: frozenset[str] = frozenset({'jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'heif', 'webp'})

VIDEO_EXTENSIONS: frozenset[str] = frozenset({'mp4', 'mov', 'avi', 'mkv'})

ALL_SUPPORTED_EXTENSIONS: frozenset[str] = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS

VIDEO_WITH_METADATA: frozenset[str] = frozenset({'mp4', 'mov'})

TARGET_NAME_PATTERN: str = r'(?:IMG|VID)_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(?:_\d+)?\.\w+'

TARGET_NAME_RE: re.Pattern[str] = re.compile(TARGET_NAME_PATTERN)

FILENAME_DATE_PATTERNS: list[tuple[str, re.Pattern[str], str | None]] = [
    (
        'target',
        re.compile(r'(?:IMG|VID)_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(?:_\d+)?'),
        None,
    ),
    (
        'ios_screenshot',
        re.compile(r'Screenshot\s+(\d{4})-(\d{2})-(\d{2})\s+at\s+(\d{2})\.(\d{2})\.(\d{2})'),
        None,
    ),
    (
        'android_screenshot',
        re.compile(r'Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})'),
        None,
    ),
    (
        'telegram',
        re.compile(r'photo_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})'),
        None,
    ),
    (
        'wechat',
        re.compile(r'mmexport(\d{14})'),
        '%Y%m%d%H%M%S',
    ),
    (
        'generic_dash_underscore',
        re.compile(r'(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})'),
        None,
    ),
    (
        'generic_underscore',
        re.compile(r'(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})'),
        None,
    ),
    (
        'generic_dot_dash',
        re.compile(r'(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})'),
        None,
    ),
    (
        'generic_dash_space',
        re.compile(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2})\.(\d{2})\.(\d{2})'),
        None,
    ),
    (
        'generic_14digit',
        re.compile(r'(?<!\d)(\d{14})(?!\d)'),
        '%Y%m%d%H%M%S',
    ),
]

EXIF_DATETIME_ORIGINAL: int = 0x9003
EXIF_DATETIME_DIGITIZED: int = 0x9004
EXIF_DATETIME: int = 0x0132

MAC_EPOCH = datetime(1904, 1, 1)

MIN_VALID_YEAR = 1970

PLAN_FILENAME = 'imgts-plan.json'

PLAN_VERSION = 1

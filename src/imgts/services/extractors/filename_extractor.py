from datetime import datetime
from pathlib import Path

from imgts.constants import FILENAME_DATE_PATTERNS
from imgts.models import DateSource, ExtractedDate
from imgts.utils import validate_year


def extract_filename_date(path: Path) -> list[ExtractedDate]:
    """Extract date from filename using multiple known patterns.

    Tries each pattern in priority order and returns the first successful match.
    Returns empty list if no pattern matches or date validation fails.
    """
    try:
        filename = path.name

        for _pattern_name, regex, fmt in FILENAME_DATE_PATTERNS:
            match = regex.search(filename)
            if not match:
                continue

            try:
                if fmt is not None:
                    dt = datetime.strptime(match.group(1), fmt)
                else:
                    year, month, day, hour, minute, second = map(int, match.groups())
                    dt = datetime(year, month, day, hour, minute, second)

                if not validate_year(dt):
                    continue

                return [
                    ExtractedDate(
                        source=DateSource.FILENAME,
                        datetime=dt,
                        raw_value=match.group(0),
                    )
                ]
            except (ValueError, IndexError):
                continue

        return []
    except Exception:
        return []

"""Data models for imgts package."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class DateSource(str, Enum):
    """Source of date/time information."""

    EXIF_ORIGINAL = 'EXIF_ORIGINAL'
    EXIF_DIGITIZED = 'EXIF_DIGITIZED'
    EXIF_MODIFY = 'EXIF_MODIFY'
    FS_CREATION = 'FS_CREATION'
    FS_MODIFICATION = 'FS_MODIFICATION'
    FILENAME = 'FILENAME'
    VIDEO_METADATA = 'VIDEO_METADATA'


class FileType(str, Enum):
    """Type of media file."""

    PHOTO = 'PHOTO'
    VIDEO = 'VIDEO'


@dataclass(frozen=True, slots=True)
class ExtractedDate:
    """Extracted date from a source."""

    source: DateSource
    datetime: datetime
    raw_value: str | None = None


@dataclass(slots=True)
class FileInfo:
    """Information about a media file."""

    path: Path
    file_type: FileType
    extension: str
    dates: list[ExtractedDate]
    size: int


@dataclass(frozen=True, slots=True)
class RenameAction:
    """Action to rename a file."""

    original_path: Path
    new_path: Path
    source: DateSource
    datetime: datetime

    def to_dict(self) -> dict[str, str]:
        """Convert to dict for JSON serialization."""
        return {
            'original_path': str(self.original_path),
            'new_path': str(self.new_path),
            'source': self.source.value,
            'datetime': self.datetime.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'RenameAction':
        """Create from dict for JSON deserialization."""
        return cls(
            original_path=Path(data['original_path']),
            new_path=Path(data['new_path']),
            source=DateSource(data['source']),
            datetime=datetime.fromisoformat(data['datetime']),
        )


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Result of scanning a directory."""

    photos: list[FileInfo]
    videos: list[FileInfo]
    skipped: list[Path]


@dataclass(frozen=True, slots=True)
class SourceStats:
    """Statistics for a date source."""

    source: DateSource
    count: int
    total: int
    min_date: datetime | None
    max_date: datetime | None


@dataclass(frozen=True, slots=True)
class ScanStats:
    """Statistics from scanning."""

    photo_stats: dict[DateSource, SourceStats]
    video_stats: dict[DateSource, SourceStats]


@dataclass
class Plan:
    """Rename plan for persistence."""

    version: int
    directory: str
    actions: list[RenameAction]
    unresolved_count: int
    created_at: str

    def to_dict(self) -> dict[str, object]:
        """Convert to dict for JSON serialization."""
        return {
            'version': self.version,
            'directory': self.directory,
            'actions': [a.to_dict() for a in self.actions],
            'unresolved_count': self.unresolved_count,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Plan':
        """Create from dict for JSON deserialization."""
        return cls(
            version=int(data['version']),
            directory=str(data['directory']),
            actions=[RenameAction.from_dict(a) for a in data['actions']],
            unresolved_count=int(data['unresolved_count']),
            created_at=str(data['created_at']),
        )

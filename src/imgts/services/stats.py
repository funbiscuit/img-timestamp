"""Statistics computation and formatting for media files."""

from collections import defaultdict

import rich
from rich.table import Table

from imgts.models import DateSource, FileInfo, ScanStats, SourceStats
from imgts.services import info


DISPLAY_NAMES: dict[DateSource, str] = {
    DateSource.EXIF_ORIGINAL: 'EXIF DateTime Original (дата съёмки)',
    DateSource.EXIF_DIGITIZED: 'EXIF DateTime Digitized',
    DateSource.EXIF_MODIFY: 'EXIF DateTime (modification)',
    DateSource.FS_CREATION: 'Filesystem creation time',
    DateSource.FS_MODIFICATION: 'Filesystem modification time',
    DateSource.FILENAME: 'Filename (various formats)',
    DateSource.VIDEO_METADATA: 'Video metadata (MP4/MOV)',
}


def compute_stats(photos: list[FileInfo], videos: list[FileInfo]) -> ScanStats:
    """Compute statistics by date source for photos and videos separately."""
    return ScanStats(
        photo_stats=_compute_source_stats(photos),
        video_stats=_compute_source_stats(videos),
    )


def _compute_source_stats(files: list[FileInfo]) -> dict[DateSource, SourceStats]:
    total = len(files)
    source_data: dict[DateSource, list[FileInfo]] = defaultdict(list)

    for f in files:
        for d in f.dates:
            source_data[d.source].append(f)

    stats: dict[DateSource, SourceStats] = {}
    for source, source_files in source_data.items():
        datetimes = [d.datetime for f in source_files for d in f.dates if d.source == source]
        min_dt = min(datetimes) if datetimes else None
        max_dt = max(datetimes) if datetimes else None
        stats[source] = SourceStats(
            source=source,
            count=len(source_files),
            total=total,
            min_date=min_dt,
            max_date=max_dt,
        )

    return stats


def format_stats(stats: ScanStats) -> None:
    """Format and display statistics as Rich tables."""
    console = rich.get_console()

    if stats.photo_stats:
        table = Table(title='Photos', show_lines=False)
        table.add_column('Source', style='cyan')
        table.add_column('Coverage', justify='right')
        table.add_column('Min Date', justify='right')
        table.add_column('Max Date', justify='right')

        for source, s in stats.photo_stats.items():
            name = DISPLAY_NAMES.get(source, source.value)
            coverage = f'{s.count}/{s.total}'
            min_str = s.min_date.strftime('%Y-%m-%d %H:%M:%S') if s.min_date else '-'
            max_str = s.max_date.strftime('%Y-%m-%d %H:%M:%S') if s.max_date else '-'
            table.add_row(name, coverage, min_str, max_str)

        console.print(table)

    if stats.video_stats:
        table = Table(title='Videos', show_lines=False)
        table.add_column('Source', style='cyan')
        table.add_column('Coverage', justify='right')
        table.add_column('Min Date', justify='right')
        table.add_column('Max Date', justify='right')

        for source, s in stats.video_stats.items():
            name = DISPLAY_NAMES.get(source, source.value)
            coverage = f'{s.count}/{s.total}'
            min_str = s.min_date.strftime('%Y-%m-%d %H:%M:%S') if s.min_date else '-'
            max_str = s.max_date.strftime('%Y-%m-%d %H:%M:%S') if s.max_date else '-'
            table.add_row(name, coverage, min_str, max_str)

        console.print(table)


def select_source(
    sources: dict[DateSource, SourceStats],
    label: str,
    allow_cancel: bool = True,
    allow_skip: bool = False,
) -> DateSource | None:
    """Display a table of sources and prompt user to select one.

    Args:
        sources: Dictionary of DateSource -> SourceStats (only sources with count > 0)
        label: Label for the prompt (e.g., 'photos', 'videos')
        allow_cancel: Whether to show cancel option
        allow_skip: Whether to show skip option

    Returns:
        Selected DateSource, or None if user chose skip/cancel
    """
    console = rich.get_console()

    table = Table(title=f'Select date source for {label}', show_lines=False)
    table.add_column('#', justify='right', style='bold')
    table.add_column('Source', style='cyan')
    table.add_column('Coverage', justify='right')
    table.add_column('Min Date', justify='right')
    table.add_column('Max Date', justify='right')

    available_sources: list[tuple[int, DateSource, SourceStats]] = []
    for idx, (source, s) in enumerate(sources.items(), 1):
        if s.count > 0:
            available_sources.append((idx, source, s))
            name = DISPLAY_NAMES.get(source, source.value)
            coverage = f'{s.count}/{s.total}'
            min_str = s.min_date.strftime('%Y-%m-%d %H:%M:%S') if s.min_date else '-'
            max_str = s.max_date.strftime('%Y-%m-%d %H:%M:%S') if s.max_date else '-'
            table.add_row(str(idx), name, coverage, min_str, max_str)

    console.print(table)

    choices = [str(idx) for idx, _, _ in available_sources]
    prompt_choices = choices.copy()

    prompt_parts = []
    if allow_skip:
        prompt_parts.append('s - skip')
        prompt_choices.append('s')
    if allow_cancel:
        prompt_parts.append('c - cancel')
        prompt_choices.append('c')

    options_str = ', '.join(prompt_parts)
    choices_str = '/'.join(prompt_choices)

    prompt = f'Your choice ({options_str}) [{choices_str}]'

    try:
        answer = info.ask(prompt, choices=prompt_choices)
    except KeyboardInterrupt:
        if allow_cancel:
            info.message('Cancelled.')
        return None

    if answer == 'c':
        if allow_cancel:
            info.message('Cancelled.')
        return None
    if answer == 's':
        return None

    idx = int(answer)
    for i, source, _ in available_sources:
        if i == idx:
            return source

    return None

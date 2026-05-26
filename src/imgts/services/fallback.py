"""Cascading fallback service for interactive source selection."""

from pathlib import Path

from imgts.models import DateSource, FileInfo, ScanStats, SourceStats
from imgts.services import info
from imgts.services.stats import compute_stats, select_source


def resolve_fallback(
    unresolved: list[FileInfo],
    scan_stats: ScanStats,
) -> dict[Path, DateSource]:
    """Resolve dates for unresolved files by offering fallback source selection.

    Shows available sources with coverage, lets user pick one.
    Recursively offers remaining sources until user skips.
    Returns mapping of file_path -> resolved DateSource.
    """
    resolved: dict[Path, DateSource] = _resolve_recursive(unresolved, scan_stats)
    return resolved


def _resolve_recursive(
    unresolved: list[FileInfo],
    original_stats: ScanStats,
) -> dict[Path, DateSource]:
    """Recursively resolve unresolved files."""
    resolved: dict[Path, DateSource] = {}

    while unresolved:
        remaining_stats = compute_stats(
            [f for f in unresolved if f.file_type.value == 'PHOTO'],
            [f for f in unresolved if f.file_type.value == 'VIDEO'],
        )

        available_sources: dict[DateSource, SourceStats] = {}
        for source_stats in remaining_stats.photo_stats.values():
            if source_stats.count > 0 and source_stats.source not in available_sources:
                available_sources[source_stats.source] = source_stats
        for source_stats in remaining_stats.video_stats.values():
            if source_stats.count > 0 and source_stats.source not in available_sources:
                available_sources[source_stats.source] = source_stats

        if not available_sources:
            info.message(f'{len(unresolved)} files have no available date sources. Skipping.')
            break

        chosen_source = select_source(
            available_sources,
            'renaming (fallback)',
            allow_cancel=True,
            allow_skip=True,
        )

        if chosen_source is None:
            info.message('Skipping remaining files.')
            break

        still_unresolved: list[FileInfo] = []
        for f in unresolved:
            has_source = any(d.source == chosen_source for d in f.dates)
            if has_source:
                resolved[f.path] = chosen_source
            else:
                still_unresolved.append(f)

        unresolved = still_unresolved

        if unresolved:
            info.message(f'{len(unresolved)} files still unresolved.')

    return resolved

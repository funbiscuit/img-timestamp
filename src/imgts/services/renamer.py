from collections import Counter

import rich
from rich.table import Table

from imgts.models import DateSource, ExtractedDate, FileInfo, RenameAction
from imgts.services import info
from imgts.utils import format_target_name


def _get_date_for_source(file: FileInfo, source: DateSource) -> ExtractedDate | None:
    """Get the first ExtractedDate matching the given source."""
    for d in file.dates:
        if d.source == source:
            return d
    return None


def build_rename_actions(
    files: list[FileInfo],
    source: DateSource,
) -> tuple[list[RenameAction], list[FileInfo]]:
    """Build rename actions for files, handling collisions and idempotency.

    Returns (actions, unresolved) where:
    - actions: list of RenameAction for files to rename
    - unresolved: files without date for the given source
    """
    actions: list[RenameAction] = []
    unresolved: list[FileInfo] = []

    candidates: list[FileInfo] = []
    for f in files:
        date = _get_date_for_source(f, source)
        if date is None:
            unresolved.append(f)
            continue

        candidates.append(f)

    target_names: list[str] = []
    for f in candidates:
        date = _get_date_for_source(f, source)
        assert date is not None
        name = format_target_name(date.datetime, f.extension, file_type=f.file_type)
        target_names.append(name)

    name_counts: Counter[str] = Counter(target_names)
    collision_tracker: Counter[str] = Counter()

    for f, name in zip(candidates, target_names, strict=True):
        if name_counts[name] > 1:
            collision_tracker[name] += 1
            if collision_tracker[name] > 1:
                suffix = collision_tracker[name] - 1
                final_name = format_target_name(
                    _get_date_for_source(f, source).datetime,  # type: ignore[union-attr]
                    f.extension,
                    suffix,
                    file_type=f.file_type,
                )
            else:
                final_name = name
        else:
            final_name = name

        actions.append(
            RenameAction(
                original_path=f.path,
                new_path=f.path.parent / final_name,
                source=source,
                datetime=_get_date_for_source(f, source).datetime,  # type: ignore[union-attr]
            )
        )

    return actions, unresolved


def apply_renames(
    actions: list[RenameAction],
    dry_run: bool = True,
    title: str | None = None,
) -> tuple[int, int]:
    """Apply rename actions.

    Args:
        actions: List of rename actions
        dry_run: If True, only display plan without renaming

    Returns:
        (renamed_count, skipped_count)
    """
    if not actions:
        return 0, 0

    if dry_run:
        table = Table(title=title or 'Planned renames (dry-run)')
        table.add_column('Original', style='red')
        table.add_column('New', style='green')
        table.add_column('Source')
        table.add_column('Date', justify='right')

        for a in actions:
            table.add_row(
                a.original_path.name,
                a.new_path.name,
                a.source.value,
                a.datetime.strftime('%Y-%m-%d %H:%M:%S'),
            )

        rich.get_console().print(table)
        return len(actions), 0

    renamed = 0
    skipped = 0
    for action in actions:
        if action.original_path == action.new_path:
            continue
        try:
            action.original_path.rename(action.new_path)
            renamed += 1
        except OSError as e:
            info.warn(f'Failed to rename {action.original_path.name}: {e}')
            skipped += 1

    return renamed, skipped

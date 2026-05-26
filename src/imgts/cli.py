from datetime import datetime, timezone
from pathlib import Path

import typer

from imgts.constants import PLAN_VERSION
from imgts.errors import ExitAppError
from imgts.models import FileInfo, Plan, RenameAction
from imgts.services import info
from imgts.services.extractors import extract_dates_for_files
from imgts.services.fallback import resolve_fallback
from imgts.services.metadata_writer import update_all_metadata
from imgts.services.plan_io import delete_plan, load_plan, save_plan, validate_plan
from imgts.services.renamer import apply_renames, build_rename_actions
from imgts.services.scanner import scan_directory
from imgts.services.stats import compute_stats, select_source


app = typer.Typer(
    help='Batch rename photos and videos by embedded timestamps',
    add_completion=True,
)


def _build_plan(directory: Path) -> tuple[list[RenameAction], int]:
    with info.status('Scanning directory...'):
        scan_result = scan_directory(directory)

    all_files = scan_result.photos + scan_result.videos
    if not all_files:
        info.message('No supported files found.')
        raise typer.Exit(code=0)

    all_files = extract_dates_for_files(all_files)

    stats = compute_stats(scan_result.photos, scan_result.videos)
    if scan_result.photos and scan_result.videos:
        info.message(f'Found {len(scan_result.photos)} photos and {len(scan_result.videos)} videos.')
    elif scan_result.photos:
        info.message(f'Found {len(scan_result.photos)} photos.')
    else:
        info.message(f'Found {len(scan_result.videos)} videos.')

    photo_source = None
    video_source = None

    if scan_result.photos:
        photo_source = select_source(stats.photo_stats, 'photos', allow_cancel=True, allow_skip=False)
        if photo_source is None:
            raise typer.Exit(code=0)

    if scan_result.videos:
        video_source = select_source(stats.video_stats, 'videos', allow_cancel=True, allow_skip=False)
        if video_source is None:
            raise typer.Exit(code=0)

    actions: list[RenameAction] = []
    unresolved: list[FileInfo] = []

    if photo_source and scan_result.photos:
        photo_actions, photo_unresolved = build_rename_actions(scan_result.photos, photo_source)
        actions.extend(photo_actions)
        unresolved.extend(photo_unresolved)

    if video_source and scan_result.videos:
        video_actions, video_unresolved = build_rename_actions(scan_result.videos, video_source)
        actions.extend(video_actions)
        unresolved.extend(video_unresolved)

    if unresolved:
        info.message(f'\n{len(unresolved)} files do not have a date from the chosen source.')
        fallback_map = resolve_fallback(unresolved, stats)
        if fallback_map:
            from imgts.services.renamer import _get_date_for_source

            for f in unresolved:
                if f.path in fallback_map:
                    date = _get_date_for_source(f, fallback_map[f.path])
                    if date is not None:
                        from imgts.utils import format_target_name

                        new_name = format_target_name(date.datetime, f.extension, file_type=f.file_type)
                        new_action = RenameAction(
                            original_path=f.path,
                            new_path=f.path.parent / new_name,
                            source=fallback_map[f.path],
                            datetime=date.datetime,
                        )
                        actions.append(new_action)
            unresolved = [f for f in unresolved if f.path not in fallback_map]

    return actions, len(unresolved)


@app.callback(invoke_without_command=True)
def main_callback(
    apply: bool = typer.Option(False, '--apply', help='Apply changes (default: dry-run)'),
    directory: Path = typer.Option(Path('.'), '--directory', help='Directory to scan'),
) -> None:
    """Batch rename photos and videos by embedded timestamps."""
    if not directory.exists():
        raise ExitAppError(f'Directory not found: {directory}', code=2)
    if not directory.is_dir():
        raise ExitAppError(f'Not a directory: {directory}', code=2)

    try:
        directory = directory.resolve()
    except Exception as e:
        raise ExitAppError(f'Cannot access directory: {directory}: {e}', code=2) from None

    if apply:
        existing_plan = load_plan(directory)
        if existing_plan:
            is_valid, warnings = validate_plan(existing_plan, directory)

            if warnings:
                for w in warnings:
                    info.warn(w)

            if not is_valid or not existing_plan.actions:
                info.message('Plan is invalid or empty, replanning...')
                delete_plan(directory)
                actions, unresolved = _build_plan(directory)
            else:
                actions = existing_plan.actions
                unresolved = existing_plan.unresolved_count
        else:
            actions, unresolved = _build_plan(directory)

        while True:
            if not actions:
                info.message('No files to rename.')
                raise typer.Exit(code=0)

            info.message('')
            apply_renames(actions, dry_run=True, title='Pending renames')
            answer = info.ask('Apply these changes?', choices=['y', 'n', 'r'], default='n')

            if answer == 'r':
                delete_plan(directory)
                actions, unresolved = _build_plan(directory)
                continue
            if answer == 'n':
                raise typer.Exit(code=0)
            break

        info.message('')
        renamed_count, skipped_count = apply_renames(actions, dry_run=False)
        updated_count, failed_count = update_all_metadata(actions, dry_run=False)
        delete_plan(directory)
        info.success(
            f'Done: {renamed_count} renamed, {skipped_count} skipped, '
            f'{updated_count} metadata updated, {failed_count} metadata failures.'
        )

        if unresolved:
            raise typer.Exit(code=1)
        return

    actions, unresolved = _build_plan(directory)

    if not actions:
        info.message('No files to rename.')
        raise typer.Exit(code=0)

    info.message('')
    renamed_count, _ = apply_renames(actions, dry_run=True)

    plan = Plan(
        version=PLAN_VERSION,
        directory=str(directory),
        actions=actions,
        unresolved_count=unresolved,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    save_plan(plan, directory)
    info.success(f'Planned: {renamed_count} files to rename. Use --apply to execute.')

    if unresolved:
        raise typer.Exit(code=1)

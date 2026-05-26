"""Plan persistence functions."""

import contextlib
import json
from pathlib import Path

from imgts.constants import PLAN_FILENAME
from imgts.models import Plan, RenameAction


def save_plan(plan: Plan, directory: Path) -> Path:
    """Save plan to directory."""
    plan_path = directory / PLAN_FILENAME
    with open(plan_path, 'w') as f:
        json.dump(plan.to_dict(), f, indent=2)
    return plan_path


def load_plan(directory: Path) -> Plan | None:
    """Load plan from directory, return None if not found or invalid."""
    plan_path = directory / PLAN_FILENAME
    if not plan_path.exists():
        return None

    try:
        with open(plan_path) as f:
            data = json.load(f)
        return Plan.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def delete_plan(directory: Path) -> None:
    """Delete plan file, ignore if not exists."""
    plan_path = directory / PLAN_FILENAME
    with contextlib.suppress(FileNotFoundError):
        plan_path.unlink()


def validate_plan(plan: Plan, directory: Path) -> tuple[bool, list[str]]:
    """Validate plan against current state.

    Returns (is_valid, list_of_warnings).
    Removes invalid actions from plan.actions and returns warnings.
    """
    warnings = []
    valid_actions = []

    plan_dir = Path(plan.directory).resolve()
    target_dir = directory.resolve()

    if plan_dir != target_dir:
        warnings.append(f'Plan was created for different directory: {plan.directory}')
        return False, warnings

    for action in plan.actions:
        orig_exists = action.original_path.exists()
        target_exists = action.new_path.exists()

        if not orig_exists and target_exists:
            valid_actions.append(
                RenameAction(
                    original_path=action.new_path,
                    new_path=action.new_path,
                    source=action.source,
                    datetime=action.datetime,
                )
            )
            continue

        if not orig_exists:
            warnings.append(f'File no longer exists: {action.original_path.name}')
            continue

        if target_exists and action.original_path != action.new_path:
            warnings.append(f'Target already exists (possible partial apply): {action.new_path.name}')
            continue

        valid_actions.append(action)

    if len(valid_actions) != len(plan.actions):
        plan.actions = valid_actions

    return True, warnings

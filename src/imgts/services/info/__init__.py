import time
from types import TracebackType
from typing import IO, Any

import rich
from rich.console import Group
from rich.live import Live
from rich.progress import Progress
from rich.prompt import Prompt
from rich.spinner import Spinner


_global_live: Live | None = None
_global_group = Group()


class Status:
    def __init__(self, prefix: str):
        self._prefix = prefix
        self._status: str | None = None
        self.final_status = None
        self._spinner = Spinner('dots', style='status.spinner')
        self._spinner.start_time = 0
        self._start_time = time.time()
        self._update_spinner_text()

    @property
    def status(self) -> str | None:
        return self._status

    @status.setter
    def status(self, value: str | None) -> None:
        self._status = value
        self._update_spinner_text()

    def done(self) -> None:
        spent = time.time() - self._start_time
        self.status = f'done in {spent}s'

    def _update_spinner_text(self) -> None:
        if self._status is None:
            self._spinner.text = f'{self._prefix}...'
        else:
            self._spinner.text = f'{self._prefix}: {self._status}'

    def __enter__(self) -> 'Status':
        _add_live_renderable(self._spinner)

        if not rich.get_console().is_terminal:
            rich.print(self._spinner.text)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        _remove_live_renderable(self._spinner)
        spent = time.time() - self._start_time
        if exc_val is not None:
            if self.final_status is None:
                self.status = f'failed in {spent:.1f}s'
            error(self._spinner.text)
        else:
            if self.final_status is None:
                self.status = f'done in {spent:.1f}s'
            success(self._spinner.text)


class ProgressWrapper:
    def __init__(self, wrapped: Progress):
        self.wrapped = wrapped

    def __enter__(self) -> 'Progress':
        _add_live_renderable(self.wrapped)
        return self.wrapped

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        _remove_live_renderable(self.wrapped)
        rich.print(self.wrapped.get_renderable())


def status(text: str) -> Status:
    return Status(text)


def progress(p: Progress) -> ProgressWrapper:
    return ProgressWrapper(p)


def ask(question: str, choices: list[str] | None = None, default: Any = ...) -> str:
    if _global_live is not None:
        error('Failed to ask question due to running live widget')
        return ''

    answer = Prompt.ask(
        f'[yellow]?[/yellow] {question}',
        choices=choices,
        default=default,
    )

    return answer.strip()


def confirm(question: str, default_yes: bool = False) -> bool:
    default_val = 'y' if default_yes else 'n'
    answer = ask(question, choices=['y', 'n'], default=default_val)
    if len(answer) == 0:
        return default_yes
    else:
        return answer.lower() == 'y' or answer.lower() == 'yes'


def message(
    *objects: Any,
    sep: str = ' ',
    end: str = '\n',
    file: IO[str] | None = None,
    flush: bool = False,
) -> None:
    rich.print(*objects, sep=sep, end=end, file=file, flush=flush)


def error(text: Any) -> None:
    rich.print('[red]✗', text)


def success(text: Any) -> None:
    rich.print('[green]✓', text)


def warn(text: Any) -> None:
    rich.print('[yellow]!', text)


def _add_live_renderable(renderable: Any) -> None:
    global _global_live
    _global_group.renderables.append(renderable)
    if _global_live is None:
        _global_live = Live(_global_group, refresh_per_second=12.5, transient=True)
        _global_live.start()
    _global_live.refresh()


def _remove_live_renderable(renderable: Any) -> None:
    global _global_live
    if _global_group.renderables == [renderable]:
        assert _global_live is not None
        _global_live.stop()
        _global_live = None
    _global_group.renderables.remove(renderable)

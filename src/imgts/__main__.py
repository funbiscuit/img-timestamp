import sys

import rich

from imgts.cli import app
from imgts.errors import ExitAppError
from imgts.services import info


def handle_exception(ex: BaseException, level: int = 0) -> None:
    if type(ex) is ExitAppError:
        info.error(ex.message)
        sys.exit(ex.code)
    if level > 50:
        return

    if ex.__cause__:
        handle_exception(ex.__cause__, level + 1)
    elif ex.__context__ and not ex.__suppress_context__:
        handle_exception(ex.__context__, level + 1)


def main() -> None:
    try:
        app()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        info.message('')
        sys.exit(130)
    except Exception as e:
        handle_exception(e)
        raise e
    finally:
        rich.get_console().show_cursor(True)


if __name__ == '__main__':
    main()

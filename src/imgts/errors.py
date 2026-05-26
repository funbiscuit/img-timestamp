from dataclasses import dataclass


@dataclass
class ExitAppError(Exception):
    message: str
    code: int = 1

    def __str__(self) -> str:
        return self.message

"""Small provider contract; verdicts never include inspected text or raw errors."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class SafetyAction(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REDIRECT = "REDIRECT"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SafetyResult:
    action: SafetyAction
    reason: str
    provider: str
    safe_message: str | None = None
    findings: tuple[str, ...] = ()


@dataclass(frozen=True)
class OutputContext:
    # Only backend-rendered templates may supply this value. Never set it to a
    # candidate LLM output, browser snapshot or unvalidated dataset description.
    trusted_text: str | None = None


class SafetyProvider(Protocol):
    def inspect_input(self, text: str) -> SafetyResult: ...

    def inspect_output(self, text: str, context: OutputContext | None = None) -> SafetyResult: ...

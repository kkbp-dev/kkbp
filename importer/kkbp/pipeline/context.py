"""What every Step and Hook receives: `ctx` (docs/design/import-pipeline.md, "Context").

`ctx.game` is here for user Hooks. Built-in Steps and Hooks never read it; a test checks.
Steps get a StepContext, which adds the Game Profile; Hooks don't get the profile (v1).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from ..bundle import Bundle
from ..character import Character
from ..profiles import Profile
from .options import Options

logger = logging.getLogger("kkbp")


@dataclass(frozen=True)
class ImportContext:
    bundle: Bundle
    character: Character
    options: Options
    game: str
    log: ImportLog


@dataclass(frozen=True)
class StepContext(ImportContext):
    """What a built-in Step receives: `ctx` plus the bundle's Game Profile."""

    profile: Profile


class ImportLog:
    """Logging and user-facing reports for one import. Every line also goes to the `kkbp` logger;
    warnings are counted in the ImportResult. The pipeline writes the whole log to the bundle's
    kkbp_cache/log/log.txt."""

    def __init__(self):
        self.lines: list[str] = []
        self.warnings: list[str] = []
        self.source = "import"  # the Step or Hook running now; set by the pipeline
        self._start = time.perf_counter()

    def info(self, message: str):
        self._add(logging.INFO, message)

    def warning(self, message: str):
        self.warnings.append(f"{self.source}: {message}" if self.source != "import" else message)
        self._add(logging.WARNING, message)

    def error(self, message: str):
        self._add(logging.ERROR, message)

    def _add(self, level, message):
        seconds = time.perf_counter() - self._start
        name = logging.getLevelName(level)
        for i, part in enumerate(str(message).splitlines() or [""]):
            prefix = f"{seconds:8.2f}s {name:<7} [{self.source}] " if i == 0 else " " * 11 + " " * 8
            self.lines.append(prefix + part)
        logger.log(level, "[%s] %s", self.source, message)

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

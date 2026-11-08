"""What an import reports (docs/design/import-pipeline.md, "Running without the UI")."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class StepOutcome:
    name: str
    status: str  # ran, failed or skipped (not for this Game)
    seconds: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class HookOutcome:
    name: str
    status: str  # ran, failed, skipped (can't run here) or off (switched off)
    seconds: float = 0.0
    reason: str = ""


@dataclass
class ImportResult:
    """The outcome of one import. A failed Step stops the import and leaves the scene as it was
    when it failed; failed Hooks are warnings, and the import still counts as done."""

    ok: bool
    character_key: str | None = None
    character_name: str | None = None
    game: str | None = None
    failed_step: str | None = None
    error: str | None = None
    steps: list[StepOutcome] = field(default_factory=list)
    hooks: list[HookOutcome] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    seconds: float = 0.0
    log_path: Path | None = None

    def has_problems(self) -> bool:
        """Whether the summary shows an error or a warning, which the KKBP log explains."""
        return not self.ok or bool(self.warnings) or any(h.status == "failed" for h in self.hooks)

    def summary(self) -> list[str]:
        """The short summary the panel shows: done or failed, warnings, Hooks that didn't run."""
        if self.ok:
            lines = [f"Imported {self.character_name} ({self.seconds:.1f} s)"]
        else:
            lines = [f"Import failed in Step {self.failed_step}: {self.error}"]
        if self.warnings:
            lines.append(f"{len(self.warnings)} warning{'s' if len(self.warnings) > 1 else ''}; see the KKBP log")
        lines += [f"Hook {h.name} {h.status}: {h.reason}" for h in self.hooks if h.status in ("failed", "skipped")]
        return lines

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModuleStart:
    name: str


@dataclass
class ModuleEnd:
    name: str
    note: str | None


@dataclass
class FileCopied:
    src: Path
    dest: Path
    action: str  # "copied" | "updated" | "overwritten"


@dataclass
class FileSkipped:
    dest: Path
    reason: str  # "unchanged" | "kept local"


@dataclass
class FileConflict:
    dest: Path
    description: str


@dataclass
class SyncFile:
    src: Path
    dest: Path


@dataclass
class InstallDone:
    name: str


@dataclass
class InstallSkipped:
    name: str


@dataclass
class Warning:
    message: str


@dataclass
class Info:
    message: str


@dataclass
class SubprocessRun:
    cmd: list[str]
    cwd: Path | None = None


Event = (
    ModuleStart
    | ModuleEnd
    | FileCopied
    | FileSkipped
    | FileConflict
    | SyncFile
    | InstallDone
    | InstallSkipped
    | Warning
    | Info
    | SubprocessRun
)

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
class FileConflict:
    dest: Path
    description: str


@dataclass
class SyncFile:
    src: Path
    dest: Path


@dataclass
class InstallPackage:
    name: str
    managers: dict[str, str] | None = None  # None → use name for every PM


@dataclass
class Done:
    name: str


@dataclass
class Skipped:
    name: str
    details: str | None = None


@dataclass
class GitClone:
    url: str
    dest: Path


@dataclass
class Warning:
    message: str


@dataclass
class Info:
    message: str


@dataclass
class ActionRequired:
    message: str


@dataclass
class SubprocessRun:
    cmd: list[str]
    cwd: Path | None = None


Event = (
    ModuleStart
    | ModuleEnd
    | FileCopied
    | FileConflict
    | SyncFile
    | InstallPackage
    | Done
    | Skipped
    | GitClone
    | Warning
    | Info
    | ActionRequired
    | SubprocessRun
)

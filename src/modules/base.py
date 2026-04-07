from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from src.core.events import Event


class Module(Protocol):
    name: str

    def collect(self) -> Iterator[Event]: ...

    def bootstrap(self) -> Iterator[Event]: ...

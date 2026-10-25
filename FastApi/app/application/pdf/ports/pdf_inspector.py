from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Inspection:
    page_count: int
    encrypted: bool
    active_content: frozenset[str]  # subset of {"javascript", "launch", "embedded_file"}


class PdfInspector(ABC):
    @abstractmethod
    def inspect(self, data: bytes) -> Inspection:
        """Parse in isolation and report page count, encryption and active content."""


class ActiveContentStripper(ABC):
    @abstractmethod
    def strip(self, data: bytes) -> bytes:
        """Return a copy without JavaScript, launch actions and embedded files."""

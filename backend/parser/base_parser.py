# parsers/base_parser.py
from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, line: str) -> bool:
        """Return True if this parser can handle the line."""
        pass

    @abstractmethod
    def parse(self, line: str) -> dict:
        """Return structured dict."""
        pass

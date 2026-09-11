"""
Abstract base class every collector inherits from.
Defines the shared interface: fetch() -> list[dict], so the verification
engine never needs to know which source an event came from.

Every collector must return a list of dicts in this normalized shape:
{
    "source_platform": "windy" | "gnews" | "newsdata" | "reddit" | ...,
    "raw_text": str,
    "timestamp": datetime,
    "city": str | None,
    "state": str | None,
    "latitude": float | None,
    "longitude": float | None,
    "media_urls": list[str],
    "event_type_guess": str | None,
}
"""
from abc import ABC, abstractmethod


class BaseCollector(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Fetch raw data from the source and return normalized event dicts."""
        raise NotImplementedError

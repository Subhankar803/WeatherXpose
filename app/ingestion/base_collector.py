"""
Abstract base class every collector inherits from.
Defines the shared interface: fetch() -> list[NormalizedEvent],
so the verification engine never needs to know which source an
event came from.
"""

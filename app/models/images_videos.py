"""
Standard Python identifier alias for Images_&_Videos.py
"""
from app.models.base import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import importlib

# Re-export from Images_&_Videos
_mod = importlib.import_module("app.models.Images_&_Videos")
Images_Videos = _mod.Images_Videos

__all__ = ["Images_Videos"]

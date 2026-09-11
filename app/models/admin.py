from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base

class Admin(Base):
    __tablename__ = "admins"
    Id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    Name = Column(String(100), nullable=False)
    Email = Column(String(100), nullable=False, unique=True, index=True)
    Password = Column(String(255), nullable=False)
    Permission_Level = Column(Enum("Reviewer", "Super Admin", name="permission_level"), nullable=False, default="Reviewer")
    Last_Active = Column(DateTime, nullable=True)
    Created_at = Column(DateTime, nullable=False, default=datetime.now)

    action_logs = relationship("Action_Log", back_populates="admin")
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base

class Action_Log(Base):
    __tablename__ = "action_log"
    Id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    Admin_Id = Column(Integer, ForeignKey("admins.Id"), nullable=False)
    Report_Id = Column(Integer, ForeignKey("Reports.Id"), nullable=False)
    Action = Column(Enum("Approved", "Rejected", "On hold"), nullable=False)
    Comment = Column(Text, nullable=True)
    Review_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    admin = relationship("Admin", back_populates="action_logs")
    report = relationship("Reports", back_populates="action_logs")
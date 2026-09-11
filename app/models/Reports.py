from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base

class Reports(Base):
    __tablename__ = "Reports"
    Id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    User_Id = Column(Integer, ForeignKey("users.Id"), nullable=True)
    Source_Id = Column(Integer, ForeignKey("Sources.Id"), nullable=True)
    Report = Column(Text, nullable=False)
    Time = Column(DateTime, nullable=False, default=datetime.utcnow)
    Incident_Time = Column(DateTime, nullable=True)
    City = Column(String(250), nullable=False)
    State = Column(String(250), nullable=False)
    Latitude = Column(Float, nullable=False)
    Longitude = Column(Float, nullable=False)
    Event_Type = Column(String(100), nullable=True)
    Img_Vid_Url = Column(String(2048), nullable=True)
    Verification_Score = Column(Float, nullable=False, default=0.0)
    Verification_Status = Column(Enum("Othentic", "Fake", "Underprocess", name="verification_status"), nullable=False, default="Underprocess")
    Hint_Breakdown = Column(Text, nullable=True)  # JSON formatted score signal breakdown
    Is_AI_Generated = Column(Integer, nullable=False, default=0)
    Admin_Comment = Column(Text, nullable=True)  # Direct reviewer/admin audit comment
    Reviewed_By = Column(String(100), nullable=True)  # Name of reviewer/admin
    Review_Action = Column(String(50), nullable=True)  # Approved / Rejected / On hold
    Reviewed_at = Column(DateTime, nullable=True)  # Timestamp of review
    Created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")
    source = relationship("Source", back_populates="reports")
    images_videos = relationship("Images_Videos", back_populates="report", cascade="all, delete-orphan")
    action_logs = relationship("Action_Log", back_populates="report", cascade="all, delete-orphan")

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class Source(Base):
    __tablename__ = "Sources"
    __table_args__ = (
        UniqueConstraint("Username", "Platform", name="uq_source_username_platform"),
    )

    Id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    Username = Column(String(255), nullable=False, index=True)
    Source_Name = Column(String(255), nullable=True, index=True)
    Platform = Column(String(255), nullable=False, index=True)
    Trust_Status = Column(Enum("GREEN", "GREY", "RED", name="source_trust_status"), nullable=False, default="GREY")
    Total_Reports = Column(Integer, nullable=False, default=0)
    Fake_Reports = Column(Integer, nullable=False, default=0)
    Warnings_Count = Column(Integer, nullable=False, default=0)
    Total_Claims = Column(Integer, nullable=False, default=0)
    True_Claims = Column(Integer, nullable=False, default=0)
    False_Claims = Column(Integer, nullable=False, default=0)
    Trust_Score = Column(Float, nullable=False, default=50.0)
    First_Seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    Last_Seen = Column(DateTime, nullable=False, default=datetime.utcnow)

    reports = relationship("Reports", back_populates="source")

    def __init__(self, *args, **kwargs):
        # Auto-sync Username and Source_Name if one is missing
        if "Username" in kwargs and "Source_Name" not in kwargs:
            kwargs["Source_Name"] = kwargs["Username"]
        elif "Source_Name" in kwargs and "Username" not in kwargs:
            kwargs["Username"] = kwargs["Source_Name"]
        super().__init__(*args, **kwargs)
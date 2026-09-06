from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Computed
from sqlalchemy.orm import relationship
from app.models.base import Base

class Source(Base):
    __tablename__ = "Sources"
    Id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    Source_Name = Column(String(255), nullable=False, unique=True)
    Platform = Column(String(255), nullable=False)
    Total_Claims = Column(Integer, nullable=False, default=0)
    True_Claims = Column(Integer, nullable=False, default=0)
    False_Claims = Column(Integer, nullable=False, default=0)
    Trust_Score = Column(Float, Computed("CASE WHEN Total_Claims > 0 THEN (True_Claims / Total_Claims) * 100 ELSE 50 END"))
    First_Seen = Column(DateTime, nullable=False, default=datetime.now)
    Last_Seen = Column(DateTime, nullable=False, default=datetime.now)

    reports = relationship("Reports", back_populates="source")
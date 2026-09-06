from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, VARCHAR
from sqlalchemy.orm import relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    Id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    Name = Column(String(100), nullable=False, index=True)
    Email = Column(String(100), nullable=False, unique=True, index=True)
    Password = Column(String(100), nullable=False)
    Phone_No = Column(VARCHAR(12), unique=True, nullable=False)
    Location = Column(String(500), nullable=False)
    Is_Active = Column(Boolean, nullable=False, default=True)
    Last_Login = Column(DateTime, nullable=True)
    Created_at = Column(DateTime, nullable=False, default=datetime.now)

    reports = relationship("Reports", back_populates="user")
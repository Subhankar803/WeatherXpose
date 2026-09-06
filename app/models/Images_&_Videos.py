from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Images_Videos(Base):
    __tablename__ = "images_videos"
    Id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    Report_Id = Column(Integer, ForeignKey("Reports.Id"), nullable=False)
    Img_Hash = Column(String(255), nullable=False)
    Exif_GPS = Column(String(255), nullable=True)
    Exif_Timestamp = Column(String(255), nullable=True)
    Exif_Camera = Column(String(255), nullable=True)

    report = relationship("Reports", back_populates="images_videos")
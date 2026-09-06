from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class PermissionLevel(str, Enum):
    REVIEWER = "Reviewer"
    SUPER_ADMIN = "Super Admin"

class VerificationStatus(str, Enum):
    OTHENTIC = "Othentic"
    FAKE = "Fake"
    UNDERPROCESS = "Underprocess"

class ActionType(str, Enum):
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ON_HOLD = "On hold"

class Users(BaseModel):
    Id: Optional[int] = Field(default=None, nullable=False, unique = True)
    Name: str = Field(..., min_length=1, max_length=100, nullable=False)
    Email: str = Field(..., min_length=1, max_length=100, nullable=False, unique = True)
    Password: str = Field(..., min_length=1, max_length=255, nullable=False)
    Phone_No: Optional[str] = Field(default = None, nullable = False, unique = True)
    Location: str = Field(..., min_length=1, max_length=250, nullable=False)
    Is_Active: bool = Field(default = True, nullable = False)
    Last_Login: datetime = Field(default = datetime.now, nullable = True)
    Created_at: datetime = Field(default = datetime.now, nullable = False)

class Admin(BaseModel):
    Id: Optional[int] = Field(default=None, nullable=False, unique = True)
    Name: str = Field(..., min_length=1, max_length=100, nullable=False)
    Email: str = Field(..., min_length=1, max_length=100, nullable=False, unique = True)
    Password: str = Field(..., min_length=1, max_length=255, nullable=False)
    Phone_No: Optional[str] = Field(default = None, nullable = False, unique = True)
    Permission_Level: PermissionLevel = Field(default = PermissionLevel.REVIEWER, nullable = False)
    Last_Active: datetime = Field(default = datetime.now, nullable = True)
    Created_at: datetime = Field(default = datetime.now, nullable = False)

class Reports(BaseModel):
    Id: Optional[int] = Field(default=None, nullable=False, unique=True)
    User_Id: int = Field(..., nullable=False)
    Source_Id: int = Field(..., nullable=False)
    Report: Optional[str] = Field(default=None)
    Time: datetime = Field(default=datetime.now, nullable=False)
    City: str = Field(..., min_length=1, max_length=250, nullable=False)
    State: str = Field(..., min_length=1, max_length=250, nullable=False)
    Latitude: float = Field(..., nullable=False)
    Longitude: float = Field(..., nullable=False)
    Event_Type: Optional[str] = Field(default=None)
    Img_Vid_Url: Optional[str] = Field(default=None, max_length=2048)
    Verification_Score: float = Field(default=0.0, nullable=False)
    Verification_Status: VerificationStatus = Field(default=VerificationStatus.UNDERPROCESS, nullable=False)
    Created_at: datetime = Field(default=datetime.now, nullable=False)

class Images_Videos(BaseModel):
    Id: Optional[int] = Field(default=None, nullable=False, unique=True)
    Report_Id: int = Field(..., nullable=False)
    Img_Hash: str = Field(..., min_length=1, max_length=255, nullable=False)
    Exif_GPS: Optional[str] = Field(default=None, max_length=255, nullable=True)
    Exif_Timestamp: Optional[str] = Field(default=None, max_length=255, nullable=True)
    Exif_Camera: Optional[str] = Field(default=None, max_length=255, nullable=True)

class Source(BaseModel):
    Id: Optional[int] = Field(default=None, nullable=False, unique=True)
    Source_Name: str = Field(..., min_length=1, max_length=255, nullable=False, unique=True)
    Platform: str = Field(..., min_length=1, max_length=255, nullable=False)
    Total_Claims: int = Field(default=0, ge=0, nullable=False)
    True_Claims: int = Field(default=0, ge=0, nullable=False)
    False_Claims: int = Field(default=0, ge=0, nullable=False)
    Trust_Score: float = Field(default=50.0, ge=0.0, le=100.0, nullable=False)
    First_Seen: datetime = Field(default=datetime.now, nullable=False)
    Last_Seen: datetime = Field(default=datetime.now, nullable=False)

class Action_Log(BaseModel):
    Id: Optional[int] = Field(default=None, nullable=False, unique=True)
    Admin_Id: int = Field(..., nullable=False)
    Report_Id: int = Field(..., nullable=False)
    Action: ActionType = Field(..., nullable=False)
    Comment: Optional[str] = Field(default=None)
    Review_at: datetime = Field(default=datetime.now, nullable=False)
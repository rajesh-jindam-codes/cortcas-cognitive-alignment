import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr

class StudentBase(BaseModel):
    email: EmailStr
    name: str
    age: int
    gender: str
    department: str
    year_of_study: int
    enrollment_date: date

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    enrollment_date: Optional[date] = None

class StudentOut(StudentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
class StudentListItem(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    department: str
    year_of_study: int
    
    class Config:
        from_attributes = True

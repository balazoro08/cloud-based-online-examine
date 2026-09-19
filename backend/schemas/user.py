from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    email: EmailStr

class StudentProfileCreate(BaseModel):
    roll_number: Optional[str] = None
    department: Optional[str] = None
    year: Optional[str] = None
    section: Optional[str] = None

class TeacherProfileCreate(BaseModel):
    department: Optional[str] = None

class UserRegister(UserBase):
    password: str
    roll_number: Optional[str] = None
    department: Optional[str] = None
    year: Optional[str] = None
    section: Optional[str] = None

class UserAdminCreate(UserBase):
    password: str
    role: str  # admin, teacher, student
    department: Optional[str] = None
    roll_number: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str
    email: str

class StudentResponse(BaseModel):
    id: int
    roll_number: Optional[str] = None
    department: Optional[str] = None
    year: Optional[str] = None
    section: Optional[str] = None

    class Config:
        from_attributes = True

class TeacherResponse(BaseModel):
    id: int
    department: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime
    student_profile: Optional[StudentResponse] = None
    teacher_profile: Optional[TeacherResponse] = None

    class Config:
        from_attributes = True

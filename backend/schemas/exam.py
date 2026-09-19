from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from backend.schemas.question import QuestionResponse

class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ExamCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subject_id: int
    duration_minutes: int = 60
    total_marks: float = 100.0
    passing_percentage: float = 40.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject_id: Optional[int] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[float] = None
    passing_percentage: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ExamResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    subject_id: int
    teacher_id: int
    duration_minutes: int
    total_marks: float
    passing_percentage: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    created_at: datetime
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    question_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ExamDetailResponse(ExamResponse):
    questions: List[QuestionResponse] = []

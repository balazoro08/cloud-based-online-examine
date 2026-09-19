from typing import List, Optional
from pydantic import BaseModel

class OptionCreate(BaseModel):
    option_text: str
    is_correct: bool = False

class OptionResponse(BaseModel):
    id: int
    option_text: str
    is_correct: bool

    class Config:
        from_attributes = True

class OptionStudentResponse(BaseModel):
    id: int
    option_text: str

    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    question_text: str
    marks: float = 1.0
    question_order: Optional[int] = 1
    options: List[OptionCreate]

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    marks: Optional[float] = None
    question_order: Optional[int] = None
    options: Optional[List[OptionCreate]] = None

class QuestionResponse(BaseModel):
    id: int
    exam_id: int
    question_text: str
    marks: float
    question_order: int
    options: List[OptionResponse]

    class Config:
        from_attributes = True

class QuestionStudentResponse(BaseModel):
    id: int
    exam_id: int
    question_text: str
    marks: float
    question_order: int
    options: List[OptionStudentResponse]

    class Config:
        from_attributes = True

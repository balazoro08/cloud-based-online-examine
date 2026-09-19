from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from backend.schemas.question import QuestionStudentResponse

class AnswerSaveRequest(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None

class AnswerSaveResponse(BaseModel):
    attempt_id: int
    question_id: int
    selected_option_id: Optional[int] = None
    saved: bool = True

class AttemptStartResponse(BaseModel):
    attempt_id: int
    exam_id: int
    exam_title: str
    duration_minutes: int
    total_marks: float
    passing_percentage: float
    started_at: datetime
    remaining_seconds: int
    questions: List[QuestionStudentResponse]
    saved_answers: dict = {}  # {question_id: selected_option_id}

class AnswerDetailResponse(BaseModel):
    question_id: int
    question_text: str
    selected_option_id: Optional[int] = None
    selected_option_text: Optional[str] = None
    correct_option_id: Optional[int] = None
    correct_option_text: Optional[str] = None
    is_correct: Optional[bool] = False
    marks_obtained: float = 0.0
    total_marks: float = 1.0

class ExamResultResponse(BaseModel):
    attempt_id: int
    exam_id: int
    exam_title: str
    subject_name: Optional[str] = None
    student_id: int
    student_name: str
    student_roll: Optional[str] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None
    status: str
    score: float
    total_marks: float
    percentage: float
    passing_percentage: float
    is_passed: bool
    total_questions: int
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    answers: Optional[List[AnswerDetailResponse]] = None

    class Config:
        from_attributes = True

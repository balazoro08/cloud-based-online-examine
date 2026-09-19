from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import Exam, Teacher, Subject, User, Question
from backend.schemas.exam import ExamCreate, ExamUpdate, ExamResponse, ExamDetailResponse
from backend.utils.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api/exams", tags=["Exams"])

def format_exam_response(exam: Exam, db: Session) -> ExamResponse:
    subject = db.query(Subject).filter(Subject.id == exam.subject_id).first()
    teacher = db.query(Teacher).filter(Teacher.id == exam.teacher_id).first()
    teacher_name = teacher.user.name if (teacher and teacher.user) else "Unknown"
    q_count = db.query(Question).filter(Question.exam_id == exam.id).count()

    return ExamResponse(
        id=exam.id,
        title=exam.title,
        description=exam.description,
        subject_id=exam.subject_id,
        teacher_id=exam.teacher_id,
        duration_minutes=exam.duration_minutes,
        total_marks=exam.total_marks,
        passing_percentage=exam.passing_percentage,
        start_time=exam.start_time,
        end_time=exam.end_time,
        status=exam.status,
        created_at=exam.created_at,
        subject_name=subject.name if subject else "General",
        teacher_name=teacher_name,
        question_count=q_count
    )

@router.get("", response_model=List[ExamResponse])
def get_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        exams = db.query(Exam).order_by(Exam.id.desc()).all()
    elif current_user.role == "teacher":
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
        if not teacher:
            return []
        exams = db.query(Exam).filter(Exam.teacher_id == teacher.id).order_by(Exam.id.desc()).all()
    else:  # student
        exams = db.query(Exam).filter(Exam.status == "published").order_by(Exam.id.desc()).all()
    
    return [format_exam_response(e, db) for e in exams]

@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(
    exam_data: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher and current_user.role == "teacher":
        raise HTTPException(status_code=400, detail="Teacher profile not found")
    
    teacher_id = teacher.id if teacher else 1  # Fallback for admin

    subject = db.query(Subject).filter(Subject.id == exam_data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    exam = Exam(
        title=exam_data.title,
        description=exam_data.description,
        subject_id=exam_data.subject_id,
        teacher_id=teacher_id,
        duration_minutes=exam_data.duration_minutes,
        total_marks=exam_data.total_marks,
        passing_percentage=exam_data.passing_percentage,
        start_time=exam_data.start_time,
        end_time=exam_data.end_time,
        status="draft"
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return format_exam_response(exam, db)

@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return format_exam_response(exam, db)

@router.put("/{exam_id}", response_model=ExamResponse)
def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if exam_data.title is not None:
        exam.title = exam_data.title
    if exam_data.description is not None:
        exam.description = exam_data.description
    if exam_data.subject_id is not None:
        exam.subject_id = exam_data.subject_id
    if exam_data.duration_minutes is not None:
        exam.duration_minutes = exam_data.duration_minutes
    if exam_data.total_marks is not None:
        exam.total_marks = exam_data.total_marks
    if exam_data.passing_percentage is not None:
        exam.passing_percentage = exam_data.passing_percentage
    if exam_data.start_time is not None:
        exam.start_time = exam_data.start_time
    if exam_data.end_time is not None:
        exam.end_time = exam_data.end_time

    db.commit()
    db.refresh(exam)
    return format_exam_response(exam, db)

@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    db.delete(exam)
    db.commit()
    return None

@router.post("/{exam_id}/publish", response_model=ExamResponse)
def publish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    q_count = db.query(Question).filter(Question.exam_id == exam_id).count()
    if q_count == 0:
        raise HTTPException(status_code=400, detail="Cannot publish exam without questions")

    exam.status = "published"
    db.commit()
    db.refresh(exam)
    return format_exam_response(exam, db)

@router.post("/{exam_id}/unpublish", response_model=ExamResponse)
def unpublish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam.status = "draft"
    db.commit()
    db.refresh(exam)
    return format_exam_response(exam, db)

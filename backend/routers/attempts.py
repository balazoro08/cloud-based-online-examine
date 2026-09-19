from datetime import datetime
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import Exam, ExamAttempt, Question, Student, User, Answer, Option
from backend.schemas.result import AttemptStartResponse, AnswerSaveRequest, AnswerSaveResponse
from backend.schemas.question import QuestionStudentResponse, OptionStudentResponse
from backend.services.exam_service import can_student_take_exam
from backend.services.evaluation_service import evaluate_attempt
from backend.utils.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["Exam Attempts"])

@router.post("/exams/{exam_id}/start", response_model=AttemptStartResponse)
def start_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student"]))
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student profile not found")

    allowed, message = can_student_take_exam(student.id, exam_id, db)
    if not allowed:
        raise HTTPException(status_code=400, detail=message)

    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    # Check for existing in-progress attempt
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.student_id == student.id,
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.status == "in_progress"
    ).first()

    if not attempt:
        attempt = ExamAttempt(
            exam_id=exam_id,
            student_id=student.id,
            started_at=datetime.utcnow(),
            status="in_progress"
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

    # Calculate remaining seconds server-side
    now = datetime.utcnow()
    started_at = attempt.started_at or now
    elapsed_seconds = max(0, int((now - started_at).total_seconds()))
    total_exam_seconds = exam.duration_minutes * 60
    remaining_seconds = max(0, total_exam_seconds - elapsed_seconds)

    # Fetch questions (strip answers for student)
    questions = db.query(Question).filter(Question.exam_id == exam_id).order_by(Question.question_order.asc(), Question.id.asc()).all()
    student_questions = []
    for q in questions:
        opts = [OptionStudentResponse(id=o.id, option_text=o.option_text) for o in q.options]
        student_questions.append(
            QuestionStudentResponse(
                id=q.id,
                exam_id=q.exam_id,
                question_text=q.question_text,
                marks=q.marks,
                question_order=q.question_order,
                options=opts
            )
        )

    # Fetch previously saved answers for autosave resume
    saved_answers_records = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    saved_answers: Dict[int, int] = {}
    for sa in saved_answers_records:
        if sa.selected_option_id:
            saved_answers[sa.question_id] = sa.selected_option_id

    return AttemptStartResponse(
        attempt_id=attempt.id,
        exam_id=exam.id,
        exam_title=exam.title,
        duration_minutes=exam.duration_minutes,
        total_marks=exam.total_marks,
        passing_percentage=exam.passing_percentage,
        started_at=started_at,
        remaining_seconds=remaining_seconds,
        questions=student_questions,
        saved_answers=saved_answers
    )

@router.get("/attempts/{attempt_id}", response_model=AttemptStartResponse)
def get_attempt_status(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
    now = datetime.utcnow()
    started_at = attempt.started_at or now
    elapsed_seconds = max(0, int((now - started_at).total_seconds()))
    total_exam_seconds = exam.duration_minutes * 60
    remaining_seconds = max(0, total_exam_seconds - elapsed_seconds)

    questions = db.query(Question).filter(Question.exam_id == exam.id).order_by(Question.question_order.asc(), Question.id.asc()).all()

    student_questions = []
    for q in questions:
        opts = [OptionStudentResponse(id=o.id, option_text=o.option_text) for o in q.options]
        student_questions.append(
            QuestionStudentResponse(
                id=q.id,
                exam_id=q.exam_id,
                question_text=q.question_text,
                marks=q.marks,
                question_order=q.question_order,
                options=opts
            )
        )

    saved_answers_records = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    saved_answers: Dict[int, int] = {}
    for sa in saved_answers_records:
        if sa.selected_option_id:
            saved_answers[sa.question_id] = sa.selected_option_id

    return AttemptStartResponse(
        attempt_id=attempt.id,
        exam_id=exam.id,
        exam_title=exam.title,
        duration_minutes=exam.duration_minutes,
        total_marks=exam.total_marks,
        passing_percentage=exam.passing_percentage,
        started_at=started_at,
        remaining_seconds=remaining_seconds,
        questions=student_questions,
        saved_answers=saved_answers
    )

@router.post("/attempts/{attempt_id}/answers", response_model=AnswerSaveResponse)
def save_answer(
    attempt_id: int,
    payload: AnswerSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student"]))
):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="Exam has already been submitted or expired")

    # Check question belongs to attempt exam
    question = db.query(Question).filter(Question.id == payload.question_id, Question.exam_id == attempt.exam_id).first()
    if not question:
        raise HTTPException(status_code=400, detail="Invalid question ID for this exam")

    # Verify option if provided
    if payload.selected_option_id:
        option = db.query(Option).filter(Option.id == payload.selected_option_id, Option.question_id == payload.question_id).first()
        if not option:
            raise HTTPException(status_code=400, detail="Invalid option selected")

    existing_answer = db.query(Answer).filter(
        Answer.attempt_id == attempt_id,
        Answer.question_id == payload.question_id
    ).first()

    if existing_answer:
        existing_answer.selected_option_id = payload.selected_option_id
    else:
        new_answer = Answer(
            attempt_id=attempt_id,
            question_id=payload.question_id,
            selected_option_id=payload.selected_option_id
        )
        db.add(new_answer)

    db.commit()
    return AnswerSaveResponse(
        attempt_id=attempt_id,
        question_id=payload.question_id,
        selected_option_id=payload.selected_option_id,
        saved=True
    )

@router.post("/attempts/{attempt_id}/submit")
def submit_exam_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["student"]))
):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.status == "submitted":
        return {"message": "Exam already submitted", "attempt_id": attempt.id}

    evaluated_attempt = evaluate_attempt(attempt_id, db)
    return {
        "message": "Exam submitted and evaluated successfully",
        "attempt_id": evaluated_attempt.id,
        "score": evaluated_attempt.score,
        "percentage": evaluated_attempt.percentage
    }

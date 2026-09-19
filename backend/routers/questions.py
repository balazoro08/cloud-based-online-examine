from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import Question, Option, Exam, User
from backend.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionStudentResponse,
    OptionResponse, OptionStudentResponse
)
from backend.utils.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["Questions & Options"])

@router.post("/exams/{exam_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    exam_id: int,
    q_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if not q_data.options or len(q_data.options) < 2:
        raise HTTPException(status_code=400, detail="Each MCQ question must have at least 2 options")

    has_correct = any(opt.is_correct for opt in q_data.options)
    if not has_correct:
        raise HTTPException(status_code=400, detail="Must mark at least one option as correct")

    question = Question(
        exam_id=exam_id,
        question_text=q_data.question_text,
        marks=q_data.marks,
        question_order=q_data.question_order or 1
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    for opt in q_data.options:
        option = Option(
            question_id=question.id,
            option_text=opt.option_text,
            is_correct=opt.is_correct
        )
        db.add(option)
    
    db.commit()
    db.refresh(question)
    return question

@router.get("/exams/{exam_id}/questions", response_model=Union[List[QuestionResponse], List[QuestionStudentResponse]])
def get_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    questions = db.query(Question).filter(Question.exam_id == exam_id).order_by(Question.question_order.asc(), Question.id.asc()).all()

    if current_user.role == "student":
        # Strip correct answers for students!
        student_questions = []
        for q in questions:
            student_opts = [OptionStudentResponse(id=opt.id, option_text=opt.option_text) for opt in q.options]
            student_questions.append(
                QuestionStudentResponse(
                    id=q.id,
                    exam_id=q.exam_id,
                    question_text=q.question_text,
                    marks=q.marks,
                    question_order=q.question_order,
                    options=student_opts
                )
            )
        return student_questions

    return questions

@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    q_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if q_data.question_text is not None:
        question.question_text = q_data.question_text
    if q_data.marks is not None:
        question.marks = q_data.marks
    if q_data.question_order is not None:
        question.question_order = q_data.question_order

    if q_data.options is not None:
        if len(q_data.options) < 2:
            raise HTTPException(status_code=400, detail="Must have at least 2 options")
        if not any(opt.is_correct for opt in q_data.options):
            raise HTTPException(status_code=400, detail="Must mark at least one option as correct")
        
        # Delete old options
        db.query(Option).filter(Option.question_id == question_id).delete()
        for opt in q_data.options:
            option = Option(
                question_id=question_id,
                option_text=opt.option_text,
                is_correct=opt.is_correct
            )
            db.add(option)

    db.commit()
    db.refresh(question)
    return question

@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(question)
    db.commit()
    return None

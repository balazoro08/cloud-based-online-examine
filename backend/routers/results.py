from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.database import get_db
from backend.database.models import ExamAttempt, Exam, Question, Option, Answer, Student, User, Subject, Teacher
from backend.schemas.result import ExamResultResponse, AnswerDetailResponse
from backend.utils.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["Results & Analytics"])

def build_result_response(attempt: ExamAttempt, db: Session, include_answers: bool = True) -> ExamResultResponse:
    exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
    student = db.query(Student).filter(Student.id == attempt.student_id).first()
    student_user = student.user if (student and student.user) else None
    subject = db.query(Subject).filter(Subject.id == exam.subject_id).first() if exam else None

    questions = db.query(Question).filter(Question.exam_id == exam.id).all() if exam else []
    total_questions = len(questions)

    answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    ans_dict = {a.question_id: a for a in answers}

    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0

    answer_details: List[AnswerDetailResponse] = []

    for q in questions:
        user_ans = ans_dict.get(q.id)
        correct_opt = db.query(Option).filter(Option.question_id == q.id, Option.is_correct == True).first()

        selected_opt = None
        if user_ans and user_ans.selected_option_id:
            selected_opt = db.query(Option).filter(Option.id == user_ans.selected_option_id).first()

        if user_ans and user_ans.selected_option_id:
            if user_ans.is_correct:
                correct_count += 1
            else:
                incorrect_count += 1
        else:
            unanswered_count += 1

        if include_answers:
            answer_details.append(
                AnswerDetailResponse(
                    question_id=q.id,
                    question_text=q.question_text,
                    selected_option_id=user_ans.selected_option_id if user_ans else None,
                    selected_option_text=selected_opt.option_text if selected_opt else "No Answer",
                    correct_option_id=correct_opt.id if correct_opt else None,
                    correct_option_text=correct_opt.option_text if correct_opt else None,
                    is_correct=user_ans.is_correct if user_ans else False,
                    marks_obtained=user_ans.marks_obtained if user_ans else 0.0,
                    total_marks=q.marks
                )
            )

    is_passed = (attempt.percentage or 0.0) >= (exam.passing_percentage if exam else 40.0)

    return ExamResultResponse(
        attempt_id=attempt.id,
        exam_id=exam.id if exam else 0,
        exam_title=exam.title if exam else "Unknown Exam",
        subject_name=subject.name if subject else "General",
        student_id=attempt.student_id,
        student_name=student_user.name if student_user else "Unknown Student",
        student_roll=student.roll_number if student else None,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        status=attempt.status,
        score=attempt.score or 0.0,
        total_marks=exam.total_marks if exam else 100.0,
        percentage=attempt.percentage or 0.0,
        passing_percentage=exam.passing_percentage if exam else 40.0,
        is_passed=is_passed,
        total_questions=total_questions,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unanswered_count=unanswered_count,
        answers=answer_details if include_answers else None
    )

@router.get("/results", response_model=List[ExamResultResponse])
def get_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        attempts = db.query(ExamAttempt).filter(ExamAttempt.status == "submitted").order_by(ExamAttempt.submitted_at.desc()).all()
    elif current_user.role == "teacher":
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
        if not teacher:
            return []
        teacher_exam_ids = [e.id for e in db.query(Exam.id).filter(Exam.teacher_id == teacher.id).all()]
        attempts = db.query(ExamAttempt).filter(
            ExamAttempt.exam_id.in_(teacher_exam_ids),
            ExamAttempt.status == "submitted"
        ).order_by(ExamAttempt.submitted_at.desc()).all()
    else:  # student
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return []
        attempts = db.query(ExamAttempt).filter(
            ExamAttempt.student_id == student.id,
            ExamAttempt.status == "submitted"
        ).order_by(ExamAttempt.submitted_at.desc()).all()

    return [build_result_response(att, db, include_answers=False) for att in attempts]

@router.get("/results/{attempt_id}", response_model=ExamResultResponse)
def get_result_detail(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Result attempt not found")
    
    # Check permissions
    if current_user.role == "student":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student or attempt.student_id != student.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    return build_result_response(attempt, db, include_answers=True)

@router.get("/exams/{exam_id}/results", response_model=List[ExamResultResponse])
def get_exam_results(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    attempts = db.query(ExamAttempt).filter(
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.status == "submitted"
    ).order_by(ExamAttempt.score.desc()).all()
    return [build_result_response(att, db, include_answers=False) for att in attempts]

@router.get("/students/{student_id}/results", response_model=List[ExamResultResponse])
def get_student_results(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempts = db.query(ExamAttempt).filter(
        ExamAttempt.student_id == student_id,
        ExamAttempt.status == "submitted"
    ).order_by(ExamAttempt.submitted_at.desc()).all()
    return [build_result_response(att, db, include_answers=False) for att in attempts]


# --- SYSTEM STATS & ANALYTICS ---

@router.get("/stats/admin")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(["admin"]))
):
    total_students = db.query(User).filter(User.role == "student").count()
    total_teachers = db.query(User).filter(User.role == "teacher").count()
    total_exams = db.query(Exam).count()
    total_subjects = db.query(Subject).count()
    active_exams = db.query(Exam).filter(Exam.status == "published").count()
    completed_attempts = db.query(ExamAttempt).filter(ExamAttempt.status == "submitted").count()

    avg_score_res = db.query(func.avg(ExamAttempt.percentage)).filter(ExamAttempt.status == "submitted").scalar()
    avg_score = round(avg_score_res, 2) if avg_score_res else 0.0

    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_exams": total_exams,
        "total_subjects": total_subjects,
        "active_exams": active_exams,
        "completed_attempts": completed_attempts,
        "average_score": avg_score
    }

@router.get("/stats/teacher")
def get_teacher_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["teacher", "admin"]))
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    teacher_id = teacher.id if teacher else 1

    teacher_exams = db.query(Exam).filter(Exam.teacher_id == teacher_id).all()
    exam_ids = [e.id for e in teacher_exams]

    total_exams = len(teacher_exams)
    active_exams = sum(1 for e in teacher_exams if e.status == "published")
    
    attempts = db.query(ExamAttempt).filter(
        ExamAttempt.exam_id.in_(exam_ids),
        ExamAttempt.status == "submitted"
    ).all() if exam_ids else []

    total_submissions = len(attempts)
    avg_score = round(sum(a.percentage for a in attempts) / total_submissions, 2) if total_submissions > 0 else 0.0

    pass_count = 0
    for a in attempts:
        exam = next((e for e in teacher_exams if e.id == a.exam_id), None)
        passing_pct = exam.passing_percentage if exam else 40.0
        if (a.percentage or 0.0) >= passing_pct:
            pass_count += 1
    
    pass_rate = round((pass_count / total_submissions * 100.0), 2) if total_submissions > 0 else 0.0

    return {
        "total_exams": total_exams,
        "active_exams": active_exams,
        "total_submissions": total_submissions,
        "average_score": avg_score,
        "pass_rate": pass_rate,
        "passed_submissions": pass_count,
        "failed_submissions": total_submissions - pass_count
    }

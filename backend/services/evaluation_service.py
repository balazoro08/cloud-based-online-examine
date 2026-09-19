from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import ExamAttempt, Question, Option, Answer, Exam

def evaluate_attempt(attempt_id: int, db: Session) -> ExamAttempt:
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise ValueError("Exam attempt not found")
    
    exam = db.query(Exam).filter(Exam.id == attempt.exam_id).first()
    if not exam:
        raise ValueError("Exam not found")

    questions = db.query(Question).filter(Question.exam_id == exam.id).all()
    
    total_obtained = 0.0
    total_exam_marks = 0.0

    for q in questions:
        total_exam_marks += q.marks
        correct_option = db.query(Option).filter(
            Option.question_id == q.id,
            Option.is_correct == True
        ).first()

        existing_answer = db.query(Answer).filter(
            Answer.attempt_id == attempt.id,
            Answer.question_id == q.id
        ).first()

        if existing_answer and existing_answer.selected_option_id:
            is_correct = (correct_option is not None and existing_answer.selected_option_id == correct_option.id)
            marks_obtained = q.marks if is_correct else 0.0
            existing_answer.is_correct = is_correct
            existing_answer.marks_obtained = marks_obtained
            total_obtained += marks_obtained
        elif existing_answer:
            existing_answer.is_correct = False
            existing_answer.marks_obtained = 0.0

    percentage = (total_obtained / total_exam_marks * 100.0) if total_exam_marks > 0 else 0.0
    
    attempt.score = round(total_obtained, 2)
    attempt.percentage = round(percentage, 2)
    attempt.status = "submitted"
    attempt.submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(attempt)
    return attempt
